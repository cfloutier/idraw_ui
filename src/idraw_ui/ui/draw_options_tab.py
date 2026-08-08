from __future__ import annotations

import customtkinter as ctk


class DrawOptionsTab:
    """Speed controls."""

    def __init__(self, window, tab: ctk.CTkFrame) -> None:
        self.window = window
        self.tab = tab
        self.build()

    def build(self) -> None:
        self.tab.grid_columnconfigure(0, weight=1)
        self.tab.grid_rowconfigure(0, weight=1)

        speed_frame = ctk.CTkFrame(self.tab, corner_radius=12)
        speed_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        speed_frame.grid_columnconfigure(0, weight=1)

        speed_header = ctk.CTkFrame(speed_frame, fg_color="transparent")
        speed_header.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 4))
        speed_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            speed_header,
            text="Speed Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            speed_header,
            text="Reset defaults",
            command=self.window.on_speed_reset_defaults,
            height=32,
        ).grid(row=0, column=1, sticky="e")

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
