from __future__ import annotations


import customtkinter as ctk


class SpeedTab:
    """Movement speed and acceleration controls."""

    def __init__(self, window, tab: ctk.CTkFrame) -> None:
        self.window = window
        self.tab = tab
        self.build()

    def build(self) -> None:
        self.tab.grid_columnconfigure(0, weight=1)
        frame = ctk.CTkFrame(self.tab, corner_radius=12)
        frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Speed Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        self.window._build_slider_block(
            frame,
            row=1,
            label="Pen-up speed",
            variable=self.window.speed_penup_var,
            command=self.window.on_speed_change,
            from_=500.0,
            to=15000.0,
        )
        self.window._build_slider_block(
            frame,
            row=2,
            label="Pen-down speed",
            variable=self.window.speed_pendown_var,
            command=self.window.on_speed_change,
            from_=200.0,
            to=12000.0,
        )
        self.window._build_slider_block(
            frame,
            row=3,
            label="Acceleration",
            variable=self.window.accel_var,
            command=self.window.on_speed_change,
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
