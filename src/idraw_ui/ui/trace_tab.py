from __future__ import annotations

import customtkinter as ctk

from idraw_ui.ui.svg_page_preview import SvgPagePreview


class TraceTab:
    """Trace tab UI for loading SVGs and running plots."""

    def __init__(self, window, tab: ctk.CTkFrame) -> None:
        self.window = window
        self.tab = tab
        self.build()

    def build(self) -> None:
        self.tab.grid_columnconfigure(0, weight=0, minsize=280)
        self.tab.grid_columnconfigure(1, weight=1, minsize=420)
        self.tab.grid_rowconfigure(0, weight=1)

        controls = ctk.CTkFrame(self.tab, corner_radius=12)
        controls.configure(width=280)
        controls.grid(row=0, column=0, sticky="nsew", padx=(4, 4), pady=4)
        controls.grid_propagate(False)
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=0)

        self.window.load_button = ctk.CTkButton(
            controls, text="Load SVG", command=self.window.on_load_svg, height=40
        )
        self.window.load_button.grid(
            row=0, column=0, sticky="ew", padx=(6, 3), pady=(6, 3)
        )

        self.window.reload_button = ctk.CTkButton(
            controls,
            text="Reload",
            command=self.window.on_reload_svg,
            width=84,
            height=40,
        )
        self.window.reload_button.grid(
            row=0, column=1, sticky="e", padx=(3, 6), pady=(6, 3)
        )

        order_row = ctk.CTkFrame(controls, fg_color="transparent")
        order_row.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=(4, 0))
        order_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(order_row, text="Reordering", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, sticky="w", padx=(2, 8)
        )
        ctk.CTkOptionMenu(
            order_row,
            values=[
                self.window._reordering_label(0),
                self.window._reordering_label(1),
                self.window._reordering_label(2),
                self.window._reordering_label(4),
            ],
            variable=self.window.reordering_var,
            command=self.window.on_reordering_change,
        ).grid(row=0, column=1, sticky="ew")

        top_separator = ctk.CTkFrame(
            controls,
            height=2,
            fg_color=("#C9D2DD", "#404550"),
        )
        top_separator.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 8)
        )

        run_bar = ctk.CTkFrame(controls, fg_color="transparent")
        run_bar.grid(row=3, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 3))
        run_bar.grid_columnconfigure(0, weight=1)
        run_bar.grid_columnconfigure(1, weight=0, minsize=8)
        run_bar.grid_columnconfigure(2, weight=1)
        run_bar.grid_columnconfigure(3, weight=0, minsize=8)
        run_bar.grid_columnconfigure(4, weight=1)
        run_bar.grid_rowconfigure(1, minsize=24)

        self.window.play_button = ctk.CTkButton(
            run_bar, text="Play", command=self.window.on_play_pause_resume, height=52
        )
        self.window.play_button.grid(row=0, column=0, sticky="ew")

        self.window.pause_button = ctk.CTkButton(
            run_bar, text="Pause", command=self.window.on_pause, height=52
        )
        self.window.pause_button.grid(row=0, column=2, sticky="ew")

        self.window.stop_button = ctk.CTkButton(
            run_bar,
            text="Stop",
            command=self.window.on_stop,
            fg_color="#B23A48",
            hover_color="#9A2F3D",
            height=52,
        )
        self.window.stop_button.grid(row=0, column=4, sticky="ew")

        ctk.CTkLabel(
            run_bar,
            textvariable=self.window.svg_bounds_warning_var,
            text_color=("#B42318", "#FF6B6B"),
            font=ctk.CTkFont(size=10, weight="bold"),
            anchor="w",
            height=24,
        ).grid(row=1, column=0, columnspan=5, sticky="ew")

        separator = ctk.CTkFrame(controls, height=2, fg_color=("#C9D2DD", "#404550"))
        separator.grid(
            row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 8)
        )

        quick_controls = ctk.CTkFrame(controls, fg_color="transparent")
        quick_controls.grid(
            row=5, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 3)
        )
        quick_controls.grid_columnconfigure((0, 1), weight=1)

        self.window.trace_home_button = ctk.CTkButton(
            quick_controls,
            text="My home",
            command=self.window.on_home,
            height=40,
        )
        self.window.trace_home_button.grid(
            row=0, column=0, sticky="ew", padx=(0, 3), pady=(0, 3)
        )

        self.window.trace_center_button = ctk.CTkButton(
            quick_controls,
            text="Center",
            command=self.window.on_center,
            height=40,
        )
        self.window.trace_center_button.grid(
            row=0, column=1, sticky="ew", padx=(3, 0), pady=(0, 3)
        )

        ctk.CTkButton(
            quick_controls,
            text="Pen Up",
            command=self.window.on_pen_up,
            height=40,
        ).grid(row=1, column=0, sticky="ew", padx=(0, 3), pady=(3, 0))

        ctk.CTkButton(
            quick_controls,
            text="Pen Down",
            command=self.window.on_pen_down,
            height=40,
        ).grid(row=1, column=1, sticky="ew", padx=(3, 0), pady=(3, 0))

        self.window.svg_page_preview = SvgPagePreview(
            self.tab,
            on_fit_changed=self.window.on_svg_page_fit_change,
        )
        self.window.svg_page_preview.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(0, 4),
            pady=4,
        )
