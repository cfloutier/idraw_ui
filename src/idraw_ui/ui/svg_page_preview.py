from __future__ import annotations

import re
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

import customtkinter as ctk

_LENGTH_PATTERN = re.compile(
    r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*([a-zA-Z]*)\s*$"
)
_MM_PER_UNIT = {
    "": 25.4 / 96.0,
    "px": 25.4 / 96.0,
    "mm": 1.0,
    "cm": 10.0,
    "in": 25.4,
    "pt": 25.4 / 72.0,
    "pc": 25.4 / 6.0,
}


@dataclass(frozen=True)
class SvgPageSize:
    width: float
    height: float
    label: str


@dataclass(frozen=True)
class PagePlacement:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def fits_table(self) -> bool:
        return self.left >= 0 and self.top >= 0

    def fits_within(
        self,
        table_width: float,
        table_height: float,
        *,
        margin_top: float = 0.0,
        margin_bottom: float = 0.0,
        margin_left: float = 0.0,
        margin_right: float = 0.0,
    ) -> bool:
        return (
            self.left >= margin_left
            and self.top >= margin_top
            and self.right <= table_width - margin_right
            and self.bottom <= table_height - margin_bottom
        )


def calculate_page_placement(
    *,
    table_width: float,
    table_height: float,
    page_width: float,
    page_height: float,
    home_corner: str,
    margin_top: float,
    margin_bottom: float,
    margin_left: float,
    margin_right: float,
) -> PagePlacement:
    margin_top = max(0.0, margin_top)
    margin_bottom = max(0.0, margin_bottom)
    margin_left = max(0.0, margin_left)
    margin_right = max(0.0, margin_right)
    if "left" in home_corner:
        left = margin_left
    elif "right" in home_corner:
        left = table_width - margin_right - page_width
    else:
        raise ValueError(f"Invalid home corner: {home_corner}")

    if "top" in home_corner:
        top = margin_top
    elif "bottom" in home_corner:
        top = table_height - margin_bottom - page_height
    else:
        raise ValueError(f"Invalid home corner: {home_corner}")

    return PagePlacement(
        left=left,
        top=top,
        right=left + page_width,
        bottom=top + page_height,
    )


def _parse_length_mm(value: str | None) -> float | None:
    if value is None:
        return None
    match = _LENGTH_PATTERN.fullmatch(value)
    if match is None:
        return None
    unit = match.group(2).lower()
    scale = _MM_PER_UNIT.get(unit)
    if scale is None:
        return None
    length_mm = float(match.group(1)) * scale
    return length_mm if length_mm > 0 else None


def _parse_view_box(value: str | None) -> tuple[float, float] | None:
    if value is None:
        return None
    try:
        values = [float(part) for part in re.split(r"[\s,]+", value.strip())]
    except ValueError:
        return None
    if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
        return None
    return values[2], values[3]


def read_svg_page_size(path: str | Path) -> SvgPageSize:
    root = ET.parse(str(path)).getroot()
    width_mm = _parse_length_mm(root.get("width"))
    height_mm = _parse_length_mm(root.get("height"))
    view_box = _parse_view_box(root.get("viewBox"))

    if width_mm is not None and height_mm is not None:
        return SvgPageSize(width_mm, height_mm, "mm")

    if view_box is not None:
        view_width, view_height = view_box
        if width_mm is not None:
            return SvgPageSize(
                width_mm,
                width_mm * view_height / view_width,
                "mm",
            )
        if height_mm is not None:
            return SvgPageSize(
                height_mm * view_width / view_height,
                height_mm,
                "mm",
            )
        return SvgPageSize(view_width, view_height, "SVG units")

    raise ValueError("SVG has no usable page dimensions")


def _format_size_value(value: float) -> str:
    rounded = round(value)
    if abs(value - rounded) < 0.05:
        return str(rounded)
    return f"{value:.1f}"


class SvgPagePreview:
    """Responsive preview of the loaded SVG page placed on the plotter table."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        *,
        on_fit_changed: Callable[[bool | None], None] | None = None,
    ) -> None:
        self._path: Path | None = None
        self._page_size: SvgPageSize | None = None
        self._table_width = 1.0
        self._table_height = 1.0
        self._home_corner = "top-left"
        self._margin_top = 0.0
        self._margin_bottom = 0.0
        self._margin_left = 0.0
        self._margin_right = 0.0
        self._on_fit_changed = on_fit_changed
        self._last_fit_state: bool | None = None

        self.frame = ctk.CTkFrame(parent, corner_radius=12)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(
            self.frame,
            bg="#F7F9FC",
            highlightthickness=0,
        )
        self._canvas.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self._canvas.bind("<Configure>", self._on_configure)
        self._redraw()

    def grid(self, **kwargs: object) -> None:
        self.frame.grid(**kwargs)

    def set_svg(self, path: str | Path) -> None:
        self._path = Path(path)
        try:
            self._page_size = read_svg_page_size(self._path)
        except (ET.ParseError, OSError, ValueError):
            self._page_size = None
        self._redraw()
        self._notify_fit_changed()

    def set_table(
        self,
        *,
        width_mm: float,
        height_mm: float,
        home_corner: str,
        margin_top_mm: float,
        margin_bottom_mm: float,
        margin_left_mm: float,
        margin_right_mm: float,
    ) -> None:
        self._table_width = max(1.0, float(width_mm))
        self._table_height = max(1.0, float(height_mm))
        self._home_corner = home_corner
        self._margin_top = max(0.0, float(margin_top_mm))
        self._margin_bottom = max(0.0, float(margin_bottom_mm))
        self._margin_left = max(0.0, float(margin_left_mm))
        self._margin_right = max(0.0, float(margin_right_mm))
        self._redraw()
        self._notify_fit_changed()

    def page_fits_table(self) -> bool | None:
        page = self._page_size
        if page is None or page.label != "mm":
            return None
        placement = calculate_page_placement(
            table_width=self._table_width,
            table_height=self._table_height,
            page_width=page.width,
            page_height=page.height,
            home_corner=self._home_corner,
            margin_top=self._margin_top,
            margin_bottom=self._margin_bottom,
            margin_left=self._margin_left,
            margin_right=self._margin_right,
        )
        return placement.fits_within(
            self._table_width,
            self._table_height,
            margin_top=self._margin_top,
            margin_bottom=self._margin_bottom,
            margin_left=self._margin_left,
            margin_right=self._margin_right,
        )

    def _notify_fit_changed(self) -> None:
        fit_state = self.page_fits_table()
        if fit_state == self._last_fit_state:
            return
        self._last_fit_state = fit_state
        if self._on_fit_changed is not None:
            self._on_fit_changed(fit_state)

    def _on_configure(self, _event: tk.Event) -> None:
        self._redraw()

    def _redraw(self) -> None:
        canvas = self._canvas
        canvas.delete("all")
        width = max(1, int(canvas.winfo_width()))
        height = max(1, int(canvas.winfo_height()))

        if self._path is None:
            canvas.create_text(
                width / 2,
                height / 2,
                text="No SVG loaded",
                fill="#647786",
                font=("Segoe UI", 12, "bold"),
            )
            return

        if self._page_size is None:
            canvas.create_text(
                width / 2,
                height / 2,
                text=f"{self._path.name}\nPage size unavailable",
                justify="center",
                fill="#8A4B52",
                font=("Segoe UI", 11, "bold"),
            )
            return

        page = self._page_size
        canvas.create_text(
            width / 2,
            18,
            text=self._path.name,
            fill="#29465B",
            font=("Segoe UI", 11, "bold"),
        )

        side_margin = 30.0
        top_margin = 58.0
        bottom_margin = 56.0
        available_width = max(1.0, width - (side_margin * 2))
        available_height = max(1.0, height - top_margin - bottom_margin)
        scale = min(
            available_width / self._table_width,
            available_height / self._table_height,
        )
        table_pixel_width = self._table_width * scale
        table_pixel_height = self._table_height * scale
        table_left = (width - table_pixel_width) / 2.0
        table_top = top_margin + ((available_height - table_pixel_height) / 2.0)
        table_right = table_left + table_pixel_width
        table_bottom = table_top + table_pixel_height

        canvas.create_rectangle(
            table_left,
            table_top,
            table_right,
            table_bottom,
            fill="#E8EDF2",
            outline="#526776",
            width=2,
        )

        safe_left = table_left + (self._margin_left * scale)
        safe_top = table_top + (self._margin_top * scale)
        safe_right = table_right - (self._margin_right * scale)
        safe_bottom = table_bottom - (self._margin_bottom * scale)
        safe_area_valid = safe_left < safe_right and safe_top < safe_bottom
        canvas.create_rectangle(
            safe_left,
            safe_top,
            safe_right,
            safe_bottom,
            outline="#3A7BD5" if safe_area_valid else "#B42318",
            width=2,
            dash=(5, 3),
        )

        placement_page_width = page.width
        placement_page_height = page.height
        physical_size_known = page.label == "mm"
        if not physical_size_known:
            preview_long_side = max(self._table_width, self._table_height) * 0.28
            page_long_side = max(page.width, page.height)
            placement_page_width = page.width * preview_long_side / page_long_side
            placement_page_height = page.height * preview_long_side / page_long_side

        placement = calculate_page_placement(
            table_width=self._table_width,
            table_height=self._table_height,
            page_width=placement_page_width,
            page_height=placement_page_height,
            home_corner=self._home_corner,
            margin_top=self._margin_top,
            margin_bottom=self._margin_bottom,
            margin_left=self._margin_left,
            margin_right=self._margin_right,
        )
        left = table_left + (placement.left * scale)
        top = table_top + (placement.top * scale)
        right = table_left + (placement.right * scale)
        bottom = table_top + (placement.bottom * scale)
        page_fits = placement.fits_within(
            self._table_width,
            self._table_height,
            margin_top=self._margin_top,
            margin_bottom=self._margin_bottom,
            margin_left=self._margin_left,
            margin_right=self._margin_right,
        )

        canvas.create_rectangle(
            left + 3,
            top + 4,
            right + 3,
            bottom + 4,
            fill="#C7D0D8",
            outline="",
        )
        canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill="#FFFFFF",
            outline="#2E6FA8" if page_fits else "#B42318",
            width=3,
        )

        arrow_x = (left + right) / 2.0
        page_pixel_height = bottom - top
        arrow_top = top + (page_pixel_height * 0.22)
        arrow_bottom = top + (page_pixel_height * 0.66)
        canvas.create_line(
            arrow_x,
            arrow_bottom,
            arrow_x,
            arrow_top,
            arrow="last",
            arrowshape=(12, 15, 6),
            fill="#E16B2D",
            width=4,
        )
        canvas.create_text(
            arrow_x,
            min(bottom - 9, arrow_bottom + 12),
            text="Up",
            fill="#B94F1C",
            font=("Segoe UI", 10, "bold"),
        )

        size_text = (
            f"{_format_size_value(page.width)} × "
            f"{_format_size_value(page.height)} {page.label}"
        )
        home_points = {
            "top-left": (safe_left, safe_top),
            "top-right": (safe_right, safe_top),
            "bottom-left": (safe_left, safe_bottom),
            "bottom-right": (safe_right, safe_bottom),
        }
        home_x, home_y = home_points[self._home_corner]
        canvas.create_oval(
            home_x - 7,
            home_y - 7,
            home_x + 7,
            home_y + 7,
            fill="#E16B2D",
            outline="#FFFFFF",
            width=2,
        )
        canvas.create_text(
            width / 2,
            39,
            text=f"Home: {self._home_corner}",
            fill="#B94F1C",
            font=("Segoe UI", 10, "bold"),
        )
        canvas.create_text(
            width / 2,
            height - 24,
            text=(
                size_text
                if physical_size_known
                else f"{size_text} · physical scale unavailable"
            ),
            fill="#29465B" if page_fits else "#B42318",
            font=("Segoe UI", 11, "bold"),
        )
