from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from idraw_ui.ui.tools import format_distance_mm


class JogTab:
    """Manual movement controls for homing, centering, and jogging."""

    def __init__(self, window, tab: ctk.CTkFrame) -> None:
        self.window = window
        self.tab = tab
        self.build()

    def build(self) -> None:
        self.tab.grid_columnconfigure(0, weight=1)
        self.tab.grid_rowconfigure(0, weight=1)

        frame = ctk.CTkFrame(self.tab, corner_radius=12)
        frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        frame.grid_columnconfigure(0, weight=1)

        nav_bar = ctk.CTkFrame(frame, fg_color="transparent")
        nav_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 8))
        nav_bar.grid_columnconfigure((0, 1), weight=1)

        self.window.home_button = ctk.CTkButton(
            nav_bar, text="Home", command=self.window.on_home, height=64
        )
        self.window.home_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.window.center_button = ctk.CTkButton(
            nav_bar, text="Center", command=self.window.on_center, height=64
        )
        self.window.center_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        jog_pad = ctk.CTkFrame(frame, fg_color="transparent")
        jog_pad.grid(row=1, column=0, padx=24, pady=(0, 10), sticky="nw")
        jog_pad.grid_columnconfigure((0, 1, 2), weight=0, minsize=84)
        jog_pad.grid_rowconfigure((0, 1, 2), weight=0, minsize=64)

        self.window.jog_pos_y_button = ctk.CTkButton(
            jog_pad, text="+Y", command=self.window.on_jog_pos_y, width=80, height=64
        )
        self.window.jog_pos_y_button.grid(row=0, column=1, padx=3, pady=3)

        self.window.jog_neg_x_button = ctk.CTkButton(
            jog_pad, text="-X", command=self.window.on_jog_neg_x, width=80, height=64
        )
        self.window.jog_neg_x_button.grid(row=1, column=0, padx=3, pady=3)

        self.window.jog_pos_x_button = ctk.CTkButton(
            jog_pad, text="+X", command=self.window.on_jog_pos_x, width=80, height=64
        )
        self.window.jog_pos_x_button.grid(row=1, column=2, padx=3, pady=3)

        self.window.jog_neg_y_button = ctk.CTkButton(
            jog_pad, text="-Y", command=self.window.on_jog_neg_y, width=80, height=64
        )
        self.window.jog_neg_y_button.grid(row=2, column=1, padx=3, pady=3)

        slider_row = ctk.CTkFrame(frame, fg_color="transparent")
        slider_row.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))
        slider_row.grid_columnconfigure(0, weight=1)
        slider_row.grid_columnconfigure(1, weight=0)

        value_var = tk.StringVar(
            value=f"Jog distance: {format_distance_mm(self.window.jog_distance_var.get())}"
        )

        def on_distance_change(value: float) -> None:
            value_var.set(f"Jog distance: {format_distance_mm(value)}")
            self.window.on_jog_distance_change(value)

        def reset_to_one_cm() -> None:
            self.window.jog_distance_var.set(10.0)
            on_distance_change(10.0)

        ctk.CTkLabel(
            slider_row,
            textvariable=value_var,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 3))

        ctk.CTkSlider(
            slider_row,
            from_=1.0,
            to=50.0,
            variable=self.window.jog_distance_var,
            command=on_distance_change,
            number_of_steps=49,
        ).grid(row=1, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(
            slider_row,
            text="1 cm",
            width=80,
            command=reset_to_one_cm,
        ).grid(row=1, column=1, sticky="e")
