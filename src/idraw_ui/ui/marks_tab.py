from __future__ import annotations

import tempfile
import tkinter as tk
from pathlib import Path

import customtkinter as ctk

_PAGE_SIZES_MM: dict[str, tuple[int, int]] = {
    "A0": (1189, 841),
    "A1": (841, 594),
    "A2": (594, 420),
    "A3": (420, 297),
    "A4": (297, 210),
    "A5": (210, 148),
    "A6": (148, 105),
    "Grand Raisin": (900, 650),
    "Raisin": (650, 500),
    "Demi-Raisin": (500, 325),
}

_CANVAS_MARGIN = 20
_CANVAS_TOP_MARGIN = 44
_CANVAS_BOTTOM_MARGIN = 24
_DEFAULT_CANVAS_W = 440
_DEFAULT_CANVAS_H = 360


def _generate_marks_svg(
    page_w: float, page_h: float, arm_mm: float, inset: float = 0.2
) -> str:
    arm = min(arm_mm, page_w / 2.0 - 0.5, page_h / 2.0 - 0.5)
    w, h = page_w, page_h
    i = inset  # push every corner point inward so clip doesn't eat the edges
    paths = [
        # top-left
        f"M {arm + i:.3f} {i:.3f} L {i:.3f} {i:.3f} L {i:.3f} {arm + i:.3f}",
        # top-right
        f"M {w - arm - i:.3f} {i:.3f} L {w - i:.3f} {i:.3f} L {w - i:.3f} {arm + i:.3f}",
        # bottom-left
        f"M {arm + i:.3f} {h - i:.3f} L {i:.3f} {h - i:.3f} L {i:.3f} {h - arm - i:.3f}",
        # bottom-right
        f"M {w - arm - i:.3f} {h - i:.3f} L {w - i:.3f} {h - i:.3f} L {w - i:.3f} {h - arm - i:.3f}",
    ]
    path_elements = "\n  ".join(
        f'<path d="{d}" fill="none" stroke="black" stroke-width="0.3"/>' for d in paths
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg"\n'
        f'     width="{w:.3f}mm" height="{h:.3f}mm"\n'
        f'     viewBox="0 0 {w:.3f} {h:.3f}">\n'
        f"  {path_elements}\n"
        f"</svg>\n"
    )


class MarksTab:
    """Page registration mark generator and plotter."""

    def __init__(self, window, tab: ctk.CTkFrame) -> None:
        self.window = window
        self.tab = tab
        self._page_size_var = tk.StringVar(value="A4")
        self._orientation_var = tk.StringVar(value="portrait")
        self._mark_size_var = tk.DoubleVar(value=20.0)
        self._mark_size_label_var = tk.StringVar(value="Mark arm: 20 mm")
        self._canvas: tk.Canvas | None = None
        self._tmp_svg: Path | None = None
        self.build()

    # ── build ──────────────────────────────────────────────────────────────

    def build(self) -> None:
        self.tab.grid_columnconfigure(0, weight=0)
        self.tab.grid_columnconfigure(1, weight=1)
        self.tab.grid_rowconfigure(0, weight=1)

        controls = ctk.CTkFrame(self.tab, corner_radius=12)
        controls.configure(width=270)
        controls.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=4)
        controls.grid_propagate(False)
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(
            controls,
            text="Page format",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))

        ctk.CTkOptionMenu(
            controls,
            values=list(_PAGE_SIZES_MM),
            variable=self._page_size_var,
            command=lambda _: self._redraw(),
        ).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))

        ctk.CTkSegmentedButton(
            controls,
            values=["portrait", "landscape"],
            variable=self._orientation_var,
            command=lambda _: self._redraw(),
        ).grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 12))

        ctk.CTkLabel(
            controls,
            textvariable=self._mark_size_label_var,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=3, column=0, sticky="w", padx=10, pady=(0, 2))

        ctk.CTkSlider(
            controls,
            from_=5.0,
            to=50.0,
            variable=self._mark_size_var,
            command=self._on_arm_change,
            number_of_steps=45,
        ).grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 12))

        ctk.CTkButton(
            controls,
            text="Plot marks",
            command=self._on_plot_marks,
            height=52,
        ).grid(row=6, column=0, sticky="ew", padx=10, pady=(0, 10))

        preview_frame = ctk.CTkFrame(self.tab, corner_radius=12)
        preview_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 4), pady=4)
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(
            preview_frame,
            bg="#F4F7FB",
            highlightthickness=0,
            bd=0,
            width=_DEFAULT_CANVAS_W,
            height=_DEFAULT_CANVAS_H,
        )
        self._canvas.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self._canvas.bind("<Configure>", lambda _: self._redraw())

        for var in (
            self.window.machine_model_var,
            self.window.table_orientation_var,
            self.window.machine_home_corner_var,
        ):
            var.trace_add("write", lambda *_: self._redraw())
        for v in self.window.machine_margin_vars.values():
            v.trace_add("write", lambda *_: self._redraw())

        self._redraw()

    # ── callbacks ──────────────────────────────────────────────────────────

    def _on_arm_change(self, value: float) -> None:
        rounded = round(value)
        self._mark_size_label_var.set(f"Mark arm: {rounded} mm")
        self._redraw()

    def _on_plot_marks(self) -> None:
        page_w, page_h = self._page_dimensions_mm()
        arm = round(self._mark_size_var.get())
        svg = _generate_marks_svg(page_w, page_h, arm)

        if self._tmp_svg is None:
            import os

            fd, tmp = tempfile.mkstemp(prefix="idraw_marks_", suffix=".svg")
            os.close(fd)
            self._tmp_svg = Path(tmp)

        self._tmp_svg.write_text(svg, encoding="utf-8")

        if self.window.tabs is not None:
            self.window.tabs.set("Trace")
        self.window._load_svg_and_estimate(str(self._tmp_svg))

    # ── helpers ────────────────────────────────────────────────────────────

    def _page_dimensions_mm(self) -> tuple[float, float]:
        ls_w, ls_h = _PAGE_SIZES_MM.get(self._page_size_var.get(), (297, 210))
        return (
            (ls_h, ls_w) if self._orientation_var.get() == "portrait" else (ls_w, ls_h)
        )

    def _table_dimensions_mm(self, model, orientation: str) -> tuple[float, float]:
        if orientation == "portrait":
            return float(model.height_mm), float(model.width_mm)
        return float(model.width_mm), float(model.height_mm)

    def _margin_int(self, side: str) -> int:
        v = self.window.machine_margin_vars[side].get()
        return int(v) if str(v).isdecimal() else 0

    # ── drawing ────────────────────────────────────────────────────────────

    def _redraw(self) -> None:
        canvas = self._canvas
        if canvas is None:
            return
        canvas.delete("all")
        cw = int(canvas.winfo_width()) or _DEFAULT_CANVAS_W
        ch = int(canvas.winfo_height()) or _DEFAULT_CANVAS_H

        model = self.window._machine_models_by_label.get(
            self.window.machine_model_var.get()
        )
        if model is None:
            return

        table_orientation = self.window.table_orientation_var.get().strip().lower()
        tw, th = self._table_dimensions_mm(model, table_orientation)

        avail_w = cw - _CANVAS_MARGIN * 2
        avail_h = ch - _CANVAS_TOP_MARGIN - _CANVAS_BOTTOM_MARGIN
        scale = min(avail_w / tw, avail_h / th)

        tpx_w = tw * scale
        tpx_h = th * scale
        tl = (cw - tpx_w) / 2.0
        tt = _CANVAS_TOP_MARGIN + (avail_h - tpx_h) / 2.0
        tr = tl + tpx_w
        tb = tt + tpx_h

        # Table
        canvas.create_rectangle(
            tl, tt, tr, tb, fill="#E8EDF2", outline="#526776", width=2
        )

        # Margins (usable zone)
        mt = self._margin_int("top")
        mb = self._margin_int("bottom")
        ml = self._margin_int("left")
        mr = self._margin_int("right")
        sl = tl + ml * scale
        st = tt + mt * scale
        sr = tr - mr * scale
        sb = tb - mb * scale
        if sl < sr and st < sb:
            canvas.create_rectangle(
                sl, st, sr, sb, outline="#3A7BD5", width=1, dash=(4, 3)
            )

        # Page placement
        page_w, page_h = self._page_dimensions_mm()
        corner = self.window.machine_home_corner_var.get().strip().lower()
        if "left" in corner:
            px = sl
        else:
            px = sr - page_w * scale
        if "top" in corner:
            py = st
        else:
            py = sb - page_h * scale

        ppx_w = page_w * scale
        ppx_h = page_h * scale
        page_fits = px >= tl and py >= tt and px + ppx_w <= tr and py + ppx_h <= tb

        # Page outline only (no fill) so the marks are the primary visual
        canvas.create_rectangle(
            px,
            py,
            px + ppx_w,
            py + ppx_h,
            fill="",
            outline="#2E6FA8" if page_fits else "#B42318",
            width=1,
            dash=(6, 3),
        )

        # Corner marks — drawn to scale, with minimum visible thickness
        arm_mm = self._mark_size_var.get()
        arm_px = arm_mm * scale
        mark_stroke = max(2, min(5, scale * 0.4))
        mark_color = "#1A5E9C" if page_fits else "#B42318"
        for cx, cy, dx, dy in (
            (px, py, 1, 1),
            (px + ppx_w, py, -1, 1),
            (px, py + ppx_h, 1, -1),
            (px + ppx_w, py + ppx_h, -1, -1),
        ):
            canvas.create_line(
                cx,
                cy,
                cx + dx * arm_px,
                cy,
                fill=mark_color,
                width=mark_stroke,
                capstyle="round",
            )
            canvas.create_line(
                cx,
                cy,
                cx,
                cy + dy * arm_px,
                fill=mark_color,
                width=mark_stroke,
                capstyle="round",
            )

        # Home marker
        home_pts = {
            "top-left": (sl, st),
            "top-right": (sr, st),
            "bottom-left": (sl, sb),
            "bottom-right": (sr, sb),
        }
        hx, hy = home_pts.get(corner, (sl, st))
        canvas.create_oval(
            hx - 7, hy - 7, hx + 7, hy + 7, fill="#E16B2D", outline="#FFFFFF", width=2
        )

        # Title
        page_name = self._page_size_var.get()
        page_ori = self._orientation_var.get()
        arm_rounded = round(arm_mm)
        canvas.create_text(
            cw / 2,
            18,
            text=f"{page_name} {page_ori}  ·  {page_w:.0f} × {page_h:.0f} mm  ·  arm {arm_rounded} mm",
            fill="#29465B",
            font=("Segoe UI", 10, "bold"),
        )
