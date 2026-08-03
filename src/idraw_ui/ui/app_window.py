from __future__ import annotations

from pathlib import Path
import threading
import time
import tkinter as tk
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from idraw_ui.backend.driver import Driver, DriverCommandResult
from idraw_ui.backend.models import PlotState


class AppWindow:
    """Tabbed operational UI inspired by the previous my_axi_draw workflow."""

    def __init__(self, driver: Driver) -> None:
        self.driver = driver
        self.title = "idraw_ui"
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(self.title)
        self.root.geometry("980x700")
        self.root.minsize(880, 620)

        self.status_var = tk.StringVar(value="Ready")
        self.state_var = tk.StringVar(value="State: idle")
        self.profile_var = tk.StringVar(
            value=f"Profile: {self.driver.plot_profile.name}"
        )
        self.svg_var = tk.StringVar(value="SVG: none")
        self.metrics_var = tk.StringVar(value="Estimated: - | Elapsed: - | Distance: -")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.trace_report_var = tk.StringVar(value="No SVG loaded.")
        self.pen_up_var = tk.DoubleVar(value=self.driver.plot_profile.pen_up_height)
        self.pen_down_var = tk.DoubleVar(value=self.driver.plot_profile.pen_down_height)
        self.speed_penup_var = tk.DoubleVar(value=self.driver.plot_profile.speed_penup)
        self.speed_pendown_var = tk.DoubleVar(
            value=self.driver.plot_profile.speed_pendown
        )
        self.accel_var = tk.DoubleVar(value=self.driver.plot_profile.accel)
        self.reordering_var = tk.StringVar(
            value=self._reordering_label(self.driver.plot_profile.reordering)
        )
        self.auto_rotate_var = tk.BooleanVar(value=self.driver.plot_profile.auto_rotate)
        self.preview_var = tk.BooleanVar(value=self.driver.plot_profile.preview)
        self.digest_var = tk.IntVar(value=self.driver.plot_profile.digest)

        self.status_label: ctk.CTkLabel | None = None
        self.load_button: ctk.CTkButton | None = None
        self.reload_button: ctk.CTkButton | None = None
        self.play_button: ctk.CTkButton | None = None
        self.pause_button: ctk.CTkButton | None = None
        self.stop_button: ctk.CTkButton | None = None
        self.home_button: ctk.CTkButton | None = None
        self.center_button: ctk.CTkButton | None = None
        self.jog_pos_x_button: ctk.CTkButton | None = None
        self.jog_pos_y_button: ctk.CTkButton | None = None
        self.jog_neg_x_button: ctk.CTkButton | None = None
        self.jog_neg_y_button: ctk.CTkButton | None = None
        self.connect_button: ctk.CTkButton | None = None
        self.disconnect_button: ctk.CTkButton | None = None
        self.trace_log: ctk.CTkTextbox | None = None

        self._last_loaded_svg: Path | None = None
        self._is_loading_svg = False
        self._svg_load_worker: threading.Thread | None = None
        self._loading_stage: str | None = None
        self._loading_started_at: float | None = None
        self._loading_stage_started_at: float | None = None
        self._is_manual_action_running = False
        self._manual_action_name: str | None = None
        self._manual_action_started_at: float | None = None
        self._manual_action_stop_requested = False
        self._manual_action_stop_result: DriverCommandResult | None = None
        self._manual_action_worker: threading.Thread | None = None

        self._build_layout()
        self._refresh_view()
        self.root.after(400, self._poll_progress)

    @classmethod
    def from_config_files(
        cls,
        machine_settings_path: str | Path,
        plot_profile_path: str | Path,
    ) -> "AppWindow":
        return cls(Driver.from_config_files(machine_settings_path, plot_profile_path))

    def _build_layout(self) -> None:
        root_frame = ctk.CTkFrame(self.root, corner_radius=14)
        root_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(root_frame, corner_radius=12)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            textvariable=self.profile_var,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(10, 2))
        ctk.CTkLabel(
            header,
            textvariable=self.svg_var,
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 10))

        tabs = ctk.CTkTabview(root_frame, corner_radius=12)
        tabs.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        tabs.add("Trace")
        tabs.add("Pen")
        tabs.add("Speed")
        tabs.add("Options")
        tabs.set("Trace")

        self._build_trace_tab(tabs.tab("Trace"))
        self._build_pen_tab(tabs.tab("Pen"))
        self._build_speed_tab(tabs.tab("Speed"))
        self._build_options_tab(tabs.tab("Options"))

    def _build_trace_tab(self, tab: ctk.CTkFrame) -> None:
        tab.grid_columnconfigure(0, weight=0, minsize=280)
        tab.grid_columnconfigure(1, weight=1, minsize=420)
        tab.grid_rowconfigure(0, weight=1)

        controls = ctk.CTkFrame(tab, corner_radius=12)
        controls.configure(width=280)
        controls.grid(row=0, column=0, sticky="nsew", padx=(8, 10), pady=8)
        controls.grid_propagate(False)
        controls.grid_columnconfigure(0, weight=1)

        self.load_button = ctk.CTkButton(
            controls, text="Load SVG", command=self.on_load_svg, height=40
        )
        self.load_button.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))

        self.reload_button = ctk.CTkButton(
            controls, text="Reload", command=self.on_reload_svg, height=40
        )
        self.reload_button.grid(row=1, column=0, sticky="ew", padx=12, pady=6)

        self.connect_button = ctk.CTkButton(
            controls, text="Connect", command=self.on_connect, height=40
        )
        self.connect_button.grid(row=2, column=0, sticky="ew", padx=12, pady=(18, 6))

        nav_bar = ctk.CTkFrame(controls, fg_color="transparent")
        nav_bar.grid(row=3, column=0, sticky="ew", padx=12, pady=6)
        nav_bar.grid_columnconfigure((0, 1), weight=1)

        self.home_button = ctk.CTkButton(
            nav_bar, text="Home", command=self.on_home, height=40
        )
        self.home_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.center_button = ctk.CTkButton(
            nav_bar, text="Center", command=self.on_center, height=40
        )
        self.center_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        jog_bar = ctk.CTkFrame(controls, fg_color="transparent")
        jog_bar.grid(row=4, column=0, sticky="ew", padx=12, pady=6)
        jog_bar.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.jog_pos_x_button = ctk.CTkButton(
            jog_bar, text="+10x", command=self.on_jog_pos_x, height=36
        )
        self.jog_pos_x_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.jog_pos_y_button = ctk.CTkButton(
            jog_bar, text="+10y", command=self.on_jog_pos_y, height=36
        )
        self.jog_pos_y_button.grid(row=0, column=1, sticky="ew", padx=2)

        self.jog_neg_x_button = ctk.CTkButton(
            jog_bar, text="-10x", command=self.on_jog_neg_x, height=36
        )
        self.jog_neg_x_button.grid(row=0, column=2, sticky="ew", padx=2)

        self.jog_neg_y_button = ctk.CTkButton(
            jog_bar, text="-10y", command=self.on_jog_neg_y, height=36
        )
        self.jog_neg_y_button.grid(row=0, column=3, sticky="ew", padx=(4, 0))

        run_bar = ctk.CTkFrame(controls, fg_color="transparent")
        run_bar.grid(row=5, column=0, sticky="ew", padx=12, pady=(18, 6))
        run_bar.grid_columnconfigure((0, 1, 2), weight=1)

        self.play_button = ctk.CTkButton(
            run_bar, text="Play", command=self.on_play_pause_resume, height=52
        )
        self.play_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.pause_button = ctk.CTkButton(
            run_bar, text="Pause", command=self.on_pause, height=52
        )
        self.pause_button.grid(row=0, column=1, sticky="ew", padx=3)

        self.stop_button = ctk.CTkButton(
            run_bar,
            text="Stop",
            command=self.on_stop,
            fg_color="#B23A48",
            hover_color="#9A2F3D",
            height=52,
        )
        self.stop_button.grid(row=0, column=2, sticky="ew", padx=(6, 0))

        self.disconnect_button = ctk.CTkButton(
            controls,
            text="Disconnect",
            command=self.on_disconnect,
            fg_color="#4C5B73",
            hover_color="#3E4A5D",
            height=40,
        )
        self.disconnect_button.grid(
            row=6, column=0, sticky="ew", padx=12, pady=(18, 12)
        )

        monitor = ctk.CTkFrame(tab, corner_radius=12)
        monitor.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=8)
        monitor.grid_rowconfigure(3, weight=3)
        monitor.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            monitor,
            textvariable=self.state_var,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        self.status_label = ctk.CTkLabel(
            monitor,
            textvariable=self.status_var,
            anchor="w",
            corner_radius=8,
            fg_color=("#E8ECF2", "#2A2D35"),
            justify="left",
            height=38,
        )
        self.status_label.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))

        ctk.CTkLabel(
            monitor,
            textvariable=self.metrics_var,
            anchor="w",
            justify="left",
            wraplength=700,
            font=ctk.CTkFont(size=12),
        ).grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))

        progress_frame = ctk.CTkFrame(monitor, fg_color="transparent")
        progress_frame.grid(row=3, column=0, sticky="nsew", padx=14, pady=(0, 12))
        progress_frame.grid_rowconfigure(1, weight=1)
        progress_frame.grid_columnconfigure(0, weight=1)

        progress = ctk.CTkProgressBar(progress_frame, variable=self.progress_var)
        progress.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        progress.set(0)

        self.trace_log = ctk.CTkTextbox(progress_frame, wrap="word", height=300)
        self.trace_log.grid(row=1, column=0, sticky="nsew")
        self.trace_log.insert("1.0", self.trace_report_var.get())
        self.trace_log.configure(state="disabled")

    def _build_pen_tab(self, tab: ctk.CTkFrame) -> None:
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=0)

        settings = ctk.CTkFrame(tab, corner_radius=12)
        settings.grid(row=0, column=0, sticky="nsew", padx=(8, 10), pady=8)
        settings.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            settings,
            text="Pen Height Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        self._build_slider_block(
            settings,
            row=1,
            label="Pen up height",
            variable=self.pen_up_var,
            command=self.on_pen_height_change,
            from_=0.0,
            to=10.0,
        )
        self._build_slider_block(
            settings,
            row=2,
            label="Pen down height",
            variable=self.pen_down_var,
            command=self.on_pen_height_change,
            from_=0.0,
            to=10.0,
        )

        info = ctk.CTkLabel(
            settings,
            text=(
                "Adjust the two pen heights live in the current profile. "
                "Use the test buttons on the right to physically validate the stroke gap."
            ),
            justify="left",
            wraplength=520,
        )
        info.grid(row=3, column=0, sticky="ew", padx=16, pady=(10, 14))

        tester = ctk.CTkFrame(tab, corner_radius=12)
        tester.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        tester.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tester,
            text="Pen Test",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 8))

        ctk.CTkButton(tester, text="Pen Up", command=self.on_pen_up, height=42).grid(
            row=1, column=0, sticky="ew", padx=14, pady=6
        )
        ctk.CTkButton(
            tester, text="Pen Down", command=self.on_pen_down, height=42
        ).grid(row=2, column=0, sticky="ew", padx=14, pady=6)
        ctk.CTkButton(
            tester,
            text="Connect",
            command=self.on_connect,
            fg_color="#4C5B73",
            hover_color="#3E4A5D",
            height=40,
        ).grid(row=3, column=0, sticky="ew", padx=14, pady=(18, 14))

    def _build_speed_tab(self, tab: ctk.CTkFrame) -> None:
        tab.grid_columnconfigure(0, weight=1)
        frame = ctk.CTkFrame(tab, corner_radius=12)
        frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Speed Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        self._build_slider_block(
            frame,
            row=1,
            label="Pen-up speed",
            variable=self.speed_penup_var,
            command=self.on_speed_change,
            from_=500.0,
            to=15000.0,
        )
        self._build_slider_block(
            frame,
            row=2,
            label="Pen-down speed",
            variable=self.speed_pendown_var,
            command=self.on_speed_change,
            from_=200.0,
            to=12000.0,
        )
        self._build_slider_block(
            frame,
            row=3,
            label="Acceleration",
            variable=self.accel_var,
            command=self.on_speed_change,
            from_=1.0,
            to=110.0,
        )

        ctk.CTkLabel(
            frame,
            text=(
                "These values are written into the active plot profile. "
                "They affect both preview/prepare and the runtime plotting configuration."
            ),
            justify="left",
            wraplength=600,
        ).grid(row=4, column=0, sticky="ew", padx=16, pady=(10, 14))

    def _build_options_tab(self, tab: ctk.CTkFrame) -> None:
        tab.grid_columnconfigure(0, weight=1)
        frame = ctk.CTkFrame(tab, corner_radius=12)
        frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Plot Options",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))

        ordering = ctk.CTkOptionMenu(
            frame,
            values=[
                self._reordering_label(0),
                self._reordering_label(1),
                self._reordering_label(2),
                self._reordering_label(4),
            ],
            variable=self.reordering_var,
            command=self.on_reordering_change,
        )
        ordering.grid(row=1, column=0, sticky="w", padx=16, pady=6)

        ctk.CTkSwitch(
            frame,
            text="Auto rotate to fit the page",
            variable=self.auto_rotate_var,
            command=self.on_options_change,
        ).grid(row=2, column=0, sticky="w", padx=16, pady=6)

        ctk.CTkSwitch(
            frame,
            text="Preview mode by default",
            variable=self.preview_var,
            command=self.on_options_change,
        ).grid(row=3, column=0, sticky="w", padx=16, pady=6)

        digest_row = ctk.CTkFrame(frame, fg_color="transparent")
        digest_row.grid(row=4, column=0, sticky="w", padx=16, pady=(10, 6))
        ctk.CTkLabel(digest_row, text="Digest level").grid(
            row=0, column=0, padx=(0, 10)
        )
        digest_box = ctk.CTkComboBox(
            digest_row,
            values=["1", "2", "3"],
            variable=tk.StringVar(value=str(self.digest_var.get())),
            command=self.on_digest_change,
            width=90,
        )
        digest_box.grid(row=0, column=1)

        ctk.CTkLabel(
            frame,
            text=(
                "These options mirror the plotting knobs from the previous tool: "
                "ordering first, then orientation/preview behavior."
            ),
            justify="left",
            wraplength=600,
        ).grid(row=5, column=0, sticky="ew", padx=16, pady=(12, 14))

    def _build_slider_block(
        self,
        parent: ctk.CTkFrame,
        *,
        row: int,
        label: str,
        variable: tk.DoubleVar,
        command,
        from_: float,
        to: float,
    ) -> None:
        block = ctk.CTkFrame(parent, fg_color="transparent")
        block.grid(row=row, column=0, sticky="ew", padx=16, pady=8)
        block.grid_columnconfigure(0, weight=1)
        value_var = tk.StringVar(value=self._format_float(variable.get()))

        def on_slider(value: float) -> None:
            value_var.set(self._format_float(value))
            command(value)

        ctk.CTkLabel(block, text=label, font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(block, textvariable=value_var).grid(row=0, column=1, sticky="e")
        ctk.CTkSlider(
            block,
            from_=from_,
            to=to,
            variable=variable,
            command=on_slider,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    def _format_float(self, value: float) -> str:
        if value >= 100:
            return f"{value:.0f}"
        if value >= 10:
            return f"{value:.1f}"
        return f"{value:.2f}"

    def _reordering_label(self, value: int) -> str:
        labels = {
            0: "Least",
            1: "Basic",
            2: "Full",
            4: "None",
        }
        return labels.get(value, str(value))

    def _reordering_value(self, label: str) -> int:
        mapping = {
            "Least": 0,
            "Basic": 1,
            "Full": 2,
            "None": 4,
        }
        return mapping.get(label, 0)

    def _status_colors(self, ok: bool) -> tuple[str, str]:
        if ok:
            return ("#E3F8E8", "#22422B")
        return ("#FBE4E6", "#4A252B")

    def _working_status_colors(self) -> tuple[str, str]:
        return ("#FFF3CD", "#5B4A1C")

    def _set_status_style(self, ok: bool) -> None:
        if self.status_label is None:
            return
        light, dark = self._status_colors(ok)
        self.status_label.configure(fg_color=(light, dark))

    def _set_status_working_style(self) -> None:
        if self.status_label is None:
            return
        light, dark = self._working_status_colors()
        self.status_label.configure(fg_color=(light, dark))

    def _append_trace_log(self, line: str) -> None:
        if self.trace_log is None:
            return
        timestamp = time.strftime("%H:%M:%S")
        self.trace_log.configure(state="normal")
        self.trace_log.insert("end", f"[{timestamp}] {line.rstrip()}\n")
        self.trace_log.see("end")
        self.trace_log.configure(state="disabled")

    def _append_trace_separator(self, title: str) -> None:
        self._append_trace_log(f"--- {title} ---")

    def _update_from_result(
        self,
        result: DriverCommandResult,
        *,
        action: str | None = None,
    ) -> None:
        progress = self.driver.get_progress()
        self.state_var.set(f"State: {progress.state.value}")
        action_prefix = f"[{action}] " if action else ""
        if result.ok:
            self.status_var.set(f"OK: {action_prefix}{result.message}")
            self._set_status_style(ok=True)
        else:
            self.status_var.set(f"ERROR: {action_prefix}{result.message}")
            self._set_status_style(ok=False)
        self._append_trace_log(self.status_var.get())
        self._refresh_view()

    def _refresh_view(self) -> None:
        progress = self.driver.get_progress()
        if self._is_loading_svg:
            stage = self._loading_stage or "loading"
            elapsed = 0.0
            if self._loading_stage_started_at is not None:
                elapsed = max(0.0, time.perf_counter() - self._loading_stage_started_at)
            self.state_var.set(f"State: {stage} ({elapsed:.1f}s)")
        elif self._is_manual_action_running:
            action = self._manual_action_name or "manual"
            elapsed = 0.0
            if self._manual_action_started_at is not None:
                elapsed = max(0.0, time.perf_counter() - self._manual_action_started_at)
            self.state_var.set(f"State: moving [{action}] ({elapsed:.1f}s)")
        else:
            self.state_var.set(f"State: {progress.state.value}")
        self.profile_var.set(f"Profile: {self.driver.plot_profile.name}")
        self.svg_var.set(
            f"SVG: {self._last_loaded_svg if self._last_loaded_svg is not None else 'none'}"
        )

        estimated = (
            f"{progress.estimated_seconds:.1f}s"
            if progress.estimated_seconds is not None
            else "-"
        )
        elapsed = f"{progress.elapsed_seconds:.1f}s"
        dist = f"down {progress.distance_pen_down_mm:.1f} mm | total {progress.distance_total_mm:.1f} mm"
        self.metrics_var.set(
            f"Estimated: {estimated} | Elapsed: {elapsed} | {dist} | Lifts: {progress.pen_lifts}"
        )

        completion = 0.0
        if progress.estimated_seconds and progress.estimated_seconds > 0:
            completion = min(progress.elapsed_seconds / progress.estimated_seconds, 1.0)
        self.progress_var.set(completion)

        has_svg = self._last_loaded_svg is not None
        is_loading = self._is_loading_svg
        is_manual = self._is_manual_action_running
        is_drawing = progress.state == PlotState.DRAWING
        is_paused = progress.state == PlotState.PAUSED
        can_resume = is_paused
        can_start = has_svg and not is_drawing and not is_loading and not is_manual

        if self.load_button is not None:
            self.load_button.configure(
                state="normal"
                if (not is_drawing and not is_loading and not is_manual)
                else "disabled"
            )
        if self.reload_button is not None:
            self.reload_button.configure(
                state="normal"
                if (has_svg and not is_drawing and not is_loading and not is_manual)
                else "disabled"
            )
        if self.connect_button is not None:
            self.connect_button.configure(
                state="normal" if (not is_loading and not is_manual) else "disabled"
            )
        if self.disconnect_button is not None:
            self.disconnect_button.configure(
                state="normal" if (not is_loading and not is_manual) else "disabled"
            )
        if self.home_button is not None:
            self.home_button.configure(
                state="normal"
                if (not is_drawing and not is_loading and not is_manual)
                else "disabled"
            )
        if self.center_button is not None:
            self.center_button.configure(
                state="normal"
                if (not is_drawing and not is_loading and not is_manual)
                else "disabled"
            )
        if self.jog_pos_x_button is not None:
            self.jog_pos_x_button.configure(
                state="normal"
                if (not is_drawing and not is_loading and not is_manual)
                else "disabled"
            )
        if self.jog_pos_y_button is not None:
            self.jog_pos_y_button.configure(
                state="normal"
                if (not is_drawing and not is_loading and not is_manual)
                else "disabled"
            )
        if self.jog_neg_x_button is not None:
            self.jog_neg_x_button.configure(
                state="normal"
                if (not is_drawing and not is_loading and not is_manual)
                else "disabled"
            )
        if self.jog_neg_y_button is not None:
            self.jog_neg_y_button.configure(
                state="normal"
                if (not is_drawing and not is_loading and not is_manual)
                else "disabled"
            )
        if self.play_button is not None:
            self.play_button.configure(
                text="Resume" if can_resume else "Play",
                state="normal" if (can_start or can_resume) else "disabled",
            )
        if self.pause_button is not None:
            self.pause_button.configure(
                state="normal"
                if (is_drawing and not is_loading and not is_manual)
                else "disabled"
            )
        if self.stop_button is not None:
            self.stop_button.configure(
                state="normal"
                if ((is_drawing or is_paused or is_manual) and not is_loading)
                else "disabled"
            )

    def _poll_progress(self) -> None:
        self._refresh_view()
        self.root.after(400, self._poll_progress)

    def _apply_plot_profile(self, **changes: object) -> None:
        self.driver.update_plot_profile(**changes)
        self._refresh_view()

    def on_load_svg(self) -> None:
        filename = filedialog.askopenfilename(
            defaultextension=".svg",
            filetypes=(("SVG files", "*.svg"), ("All files", "*.*")),
        )
        if not filename:
            return
        self._last_loaded_svg = Path(filename)
        self._load_svg_and_estimate(filename)

    def on_reload_svg(self) -> None:
        if self._last_loaded_svg is None:
            return
        self._load_svg_and_estimate(str(self._last_loaded_svg))

    def _load_svg_and_estimate(self, path: str) -> None:
        if self._is_loading_svg:
            self._append_trace_log("A load operation is already in progress.")
            return

        svg_name = Path(path).name
        self._append_trace_separator(f"Load SVG: {svg_name}")
        self._is_loading_svg = True
        self._loading_stage = "loading"
        self._loading_started_at = time.perf_counter()
        self._loading_stage_started_at = self._loading_started_at
        self.status_var.set(f"WORKING: [Load] {svg_name}")
        self._set_status_working_style()
        self._refresh_view()

        worker = threading.Thread(
            target=self._load_svg_and_estimate_worker,
            args=(path,),
            daemon=True,
        )
        self._svg_load_worker = worker
        worker.start()

    def _load_svg_and_estimate_worker(self, path: str) -> None:
        load_started = time.perf_counter()
        load_result: DriverCommandResult
        estimate_result: DriverCommandResult | None = None
        estimate_elapsed: float | None = None

        try:
            load_result = self.driver.load_svg(path)
            load_elapsed = time.perf_counter() - load_started

            if load_result.ok:

                def switch_to_estimating() -> None:
                    self._loading_stage = "estimating"
                    self._loading_stage_started_at = time.perf_counter()
                    self.status_var.set("WORKING: [Estimate] Running")
                    self._set_status_working_style()
                    self._refresh_view()

                self.root.after(0, switch_to_estimating)
                estimate_started = time.perf_counter()
                estimate_result = self.driver.estimate()
                estimate_elapsed = time.perf_counter() - estimate_started
        except Exception as exc:
            load_elapsed = time.perf_counter() - load_started
            load_result = DriverCommandResult(
                ok=False,
                message=f"Unexpected load failure: {exc}",
            )

        def finish_on_ui_thread() -> None:
            self._is_loading_svg = False
            self._svg_load_worker = None
            self._loading_stage = None
            self._loading_started_at = None
            self._loading_stage_started_at = None
            self._update_from_result(load_result, action="Load")
            self._append_trace_log(f"Load duration: {load_elapsed:.2f}s")

            if estimate_result is not None:
                self._update_from_result(estimate_result, action="Estimate")
                if estimate_elapsed is not None:
                    self._append_trace_log(
                        f"Estimate duration: {estimate_elapsed:.2f}s"
                    )

            self._refresh_view()

        try:
            self.root.after(0, finish_on_ui_thread)
        except RuntimeError:
            # Window may already be closed while background work is finishing.
            return

    def on_play_pause_resume(self) -> None:
        if self._is_manual_action_running:
            self._append_trace_log("Manual action in progress: wait or press Stop.")
            return
        progress = self.driver.get_progress()
        if progress.state == PlotState.PAUSED:
            self._update_from_result(self.driver.resume())
        else:
            self._update_from_result(self.driver.start())

    def on_pause(self) -> None:
        if self._is_manual_action_running:
            self._append_trace_log("Cannot pause plot while manual action is running.")
            return
        self._update_from_result(self.driver.pause())

    def on_stop(self) -> None:
        if self._is_manual_action_running:
            if self._manual_action_stop_requested:
                self._append_trace_log("Stop already requested for manual action.")
                return

            self._manual_action_stop_requested = True
            self.status_var.set("WORKING: [Stop] Stopping manual action...")
            self._set_status_working_style()
            self._append_trace_log("STOP requested for manual action.")
            self._manual_action_stop_result = self.driver.stop_manual_action()
            self._refresh_view()
            return

        self._update_from_result(self.driver.stop())

    def on_connect(self) -> None:
        self._update_from_result(self.driver.connect())

    def on_disconnect(self) -> None:
        self._update_from_result(self.driver.disconnect())

    def on_status(self) -> None:
        self._update_from_result(self.driver.status())

    def on_home(self) -> None:
        self._run_manual_action_async("Home", self.driver.home)

    def on_center(self) -> None:
        self._run_manual_action_async("Center", self.driver.center_for_test)

    def _jog(self, x_mm: float, y_mm: float, action: str) -> None:
        self._run_manual_action_async(
            action,
            lambda: self.driver.jog_for_test(x_mm, y_mm),
        )

    def _run_manual_action_async(
        self,
        action_name: str,
        action_func: Callable[[], DriverCommandResult],
    ) -> None:
        if self._is_loading_svg:
            self._append_trace_log(
                "Cannot start manual action while SVG loading is running."
            )
            return
        if self._is_manual_action_running:
            self._append_trace_log("Another manual action is already running.")
            return

        self._is_manual_action_running = True
        self._manual_action_name = action_name
        self._manual_action_started_at = time.perf_counter()
        self._manual_action_stop_requested = False
        self._manual_action_stop_result = None
        self.status_var.set(f"WORKING: [{action_name}] Running")
        self._set_status_working_style()
        self._refresh_view()

        worker = threading.Thread(
            target=self._manual_action_worker_run,
            args=(action_name, action_func),
            daemon=True,
        )
        self._manual_action_worker = worker
        worker.start()

    def _manual_action_worker_run(
        self,
        action_name: str,
        action_func: Callable[[], DriverCommandResult],
    ) -> None:
        try:
            action_result = action_func()
        except Exception as exc:
            action_result = DriverCommandResult(
                ok=False,
                message=f"Unexpected {action_name.lower()} failure: {exc}",
            )

        def finish_on_ui_thread() -> None:
            stop_requested = self._manual_action_stop_requested
            stop_result = self._manual_action_stop_result

            self._is_manual_action_running = False
            self._manual_action_name = None
            self._manual_action_started_at = None
            self._manual_action_stop_requested = False
            self._manual_action_stop_result = None
            self._manual_action_worker = None

            if stop_requested:
                final_stop_result = stop_result or DriverCommandResult(
                    ok=True,
                    message="manual action stopped",
                )
                self._update_from_result(final_stop_result, action="Stop")
            else:
                self._update_from_result(action_result, action=action_name)

            self._refresh_view()

        try:
            self.root.after(0, finish_on_ui_thread)
        except RuntimeError:
            return

    def on_jog_pos_x(self) -> None:
        self._jog(10.0, 0.0, "+10x")

    def on_jog_pos_y(self) -> None:
        self._jog(0.0, 10.0, "+10y")

    def on_jog_neg_x(self) -> None:
        self._jog(-10.0, 0.0, "-10x")

    def on_jog_neg_y(self) -> None:
        self._jog(0.0, -10.0, "-10y")

    def on_pen_up(self) -> None:
        self._update_from_result(self.driver.raise_pen())

    def on_pen_down(self) -> None:
        self._update_from_result(self.driver.lower_pen())

    def on_pen_height_change(self, _value: float) -> None:
        self._apply_plot_profile(
            pen_up_height=float(self.pen_up_var.get()),
            pen_down_height=float(self.pen_down_var.get()),
        )

    def on_speed_change(self, _value: float) -> None:
        self._apply_plot_profile(
            speed_penup=float(self.speed_penup_var.get()),
            speed_pendown=float(self.speed_pendown_var.get()),
            accel=float(self.accel_var.get()),
        )

    def on_reordering_change(self, value: str) -> None:
        self._apply_plot_profile(reordering=self._reordering_value(value))

    def on_options_change(self) -> None:
        self._apply_plot_profile(
            auto_rotate=bool(self.auto_rotate_var.get()),
            preview=bool(self.preview_var.get()),
        )

    def on_digest_change(self, value: str) -> None:
        try:
            digest = int(value)
        except ValueError:
            digest = 1
        self.digest_var.set(digest)
        self._apply_plot_profile(digest=digest)

    def show(self) -> None:
        self.root.mainloop()
