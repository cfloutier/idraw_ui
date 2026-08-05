from __future__ import annotations

import customtkinter as ctk


class JogTab:
    """Manual movement controls for homing, centering, and jogging."""

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
            text="Jog Controls",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        nav_bar = ctk.CTkFrame(frame, fg_color="transparent")
        nav_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(4, 10))
        nav_bar.grid_columnconfigure((0, 1), weight=1)

        self.window.home_button = ctk.CTkButton(
            nav_bar, text="Home", command=self.window.on_home, height=42
        )
        self.window.home_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.window.center_button = ctk.CTkButton(
            nav_bar, text="Center", command=self.window.on_center, height=42
        )
        self.window.center_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        jog_bar = ctk.CTkFrame(frame, fg_color="transparent")
        jog_bar.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 10))
        jog_bar.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.window.jog_pos_x_button = ctk.CTkButton(
            jog_bar, text="+10x", command=self.window.on_jog_pos_x, height=38
        )
        self.window.jog_pos_x_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.window.jog_pos_y_button = ctk.CTkButton(
            jog_bar, text="+10y", command=self.window.on_jog_pos_y, height=38
        )
        self.window.jog_pos_y_button.grid(row=0, column=1, sticky="ew", padx=2)

        self.window.jog_neg_x_button = ctk.CTkButton(
            jog_bar, text="-10x", command=self.window.on_jog_neg_x, height=38
        )
        self.window.jog_neg_x_button.grid(row=0, column=2, sticky="ew", padx=2)

        self.window.jog_neg_y_button = ctk.CTkButton(
            jog_bar, text="-10y", command=self.window.on_jog_neg_y, height=38
        )
        self.window.jog_neg_y_button.grid(row=0, column=3, sticky="ew", padx=(4, 0))

        ctk.CTkLabel(
            frame,
            text="Use these controls for manual moves outside a running plot.",
            justify="left",
            wraplength=620,
        ).grid(row=3, column=0, sticky="ew", padx=16, pady=(8, 14))
