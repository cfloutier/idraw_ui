from __future__ import annotations

import customtkinter as ctk


class DrawOptionsTab:
    """Combined speed and plot options controls."""

    def __init__(self, window, tab: ctk.CTkFrame) -> None:
        self.window = window
        self.tab = tab
        self.build()

    def build(self) -> None:
        self.tab.grid_columnconfigure(0, weight=2)
        self.tab.grid_columnconfigure(1, weight=1)
        self.tab.grid_rowconfigure(0, weight=1)

        speed_frame = ctk.CTkFrame(self.tab, corner_radius=12)
        speed_frame.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=4)
        speed_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            speed_frame,
            text="Speed Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(6, 4))

        self.window._build_slider_block(
            speed_frame,
            row=1,
            label="Travel speed (pen up)",
            variable=self.window.speed_penup_var,
            command=self.window.on_speed_change,
            from_=500.0,
            to=15000.0,
            warning_threshold=10000.0,
            warning_text="Warning: high travel speed",
        )
        self.window._build_slider_block(
            speed_frame,
            row=2,
            label="Drawing speed (pen down)",
            variable=self.window.speed_pendown_var,
            command=self.window.on_speed_change,
            from_=200.0,
            to=5000.0,
            warning_threshold=4000.0,
            warning_text="Warning: high drawing speed",
        )
        self.window._build_slider_block(
            speed_frame,
            row=3,
            label="Acceleration",
            variable=self.window.accel_var,
            command=self.window.on_speed_change,
            from_=1.0,
            to=110.0,
        )

        options_frame = ctk.CTkFrame(self.tab, corner_radius=12)
        options_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 4), pady=4)
        options_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            options_frame,
            text="Plot Options",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(6, 4))

        ordering = ctk.CTkOptionMenu(
            options_frame,
            values=[
                self.window._reordering_label(0),
                self.window._reordering_label(1),
                self.window._reordering_label(2),
                self.window._reordering_label(4),
            ],
            variable=self.window.reordering_var,
            command=self.window.on_reordering_change,
        )
        ordering.grid(row=1, column=0, sticky="w", padx=8, pady=3)

        ctk.CTkSwitch(
            options_frame,
            text="Auto rotate to fit the page",
            variable=self.window.auto_rotate_var,
            command=self.window.on_options_change,
        ).grid(row=2, column=0, sticky="w", padx=8, pady=3)

        ctk.CTkSwitch(
            options_frame,
            text="Preview mode by default",
            variable=self.window.preview_var,
            command=self.window.on_options_change,
        ).grid(row=3, column=0, sticky="w", padx=8, pady=3)
