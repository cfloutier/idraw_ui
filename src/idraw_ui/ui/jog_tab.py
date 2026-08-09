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
        frame.grid_columnconfigure(
            0, weight=5, minsize=500
        )  # left: jog pad + slider (fixed)
        frame.grid_columnconfigure(1, weight=0, minsize=100)  # right: position + margin

        # ── top bar (spans both columns) ──────────────────────────────────
        nav_bar = ctk.CTkFrame(frame, fg_color="transparent")
        nav_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 8))
        nav_bar.grid_columnconfigure((0, 1), weight=1)

        self.window.home_button = ctk.CTkButton(
            nav_bar, text="Home", command=self.window.on_jog_home, height=64
        )
        self.window.home_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.window.center_button = ctk.CTkButton(
            nav_bar, text="Center", command=self.window.on_jog_center, height=64
        )
        self.window.center_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        mode_row = ctk.CTkFrame(frame, fg_color="transparent")
        mode_row.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        mode_row.grid_columnconfigure(0, weight=1)
        mode_row.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            mode_row,
            text="Jog mode",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.window.jog_mode_selector = ctk.CTkSegmentedButton(
            mode_row,
            values=["physical", "table"],
            command=self.window.on_jog_mode_change,
        )
        self.window.jog_mode_selector.grid(row=0, column=1, sticky="e")
        self.window.jog_mode_selector.set(self.window.jog_mode_var.get())

        ctk.CTkLabel(
            mode_row,
            textvariable=self.window.jog_mode_description_var,
            font=ctk.CTkFont(size=12),
            text_color=("#5E5E5E", "#A9A9A9"),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        # ── right column: position display + set-margin buttons ────────────
        left = ctk.CTkFrame(frame, fg_color="transparent")
        left.grid(row=2, column=1, sticky="nsew", padx=(8, 20), pady=(0, 14))
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left,
            text="Position from home",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 2))

        ctk.CTkLabel(
            left,
            textvariable=self.window.jog_position_var,
            font=ctk.CTkFont(size=12),
            text_color=("#5E5E5E", "#A9A9A9"),
        ).grid(row=1, column=0, sticky="w")

        ctk.CTkFrame(left, height=2, fg_color=("#C9D2DD", "#404550")).grid(
            row=2, column=0, sticky="ew", pady=(10, 8)
        )

        ctk.CTkLabel(
            left,
            text="Set drawing margin",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=3, column=0, sticky="w", pady=(0, 3))

        ctk.CTkLabel(
            left,
            text="Go to Home · jog to a boundary · click to record",
            font=ctk.CTkFont(size=11),
            text_color=("#5E5E5E", "#A9A9A9"),
            wraplength=220,
            justify="left",
        ).grid(row=4, column=0, sticky="w", pady=(0, 8))

        btn_grid = ctk.CTkFrame(left, fg_color="transparent")
        btn_grid.grid(row=5, column=0, sticky="ew")
        btn_grid.grid_columnconfigure((0, 1, 2), weight=1)

        # cross layout matching the jog pad (top centre, left/right middle, bottom centre)
        for _label, _side, _r, _c in (
            ("Set Top", "top", 0, 1),
            ("Set Left", "left", 1, 0),
            ("Set Right", "right", 1, 2),
            ("Set Bottom", "bottom", 2, 1),
        ):
            ctk.CTkButton(
                btn_grid,
                text=_label,
                command=lambda s=_side: self.window.on_jog_set_margin(s),
                height=36,
            ).grid(row=_r, column=_c, sticky="ew", padx=3, pady=3)

        # ── left column: jog pad + distance slider ───────────────────────
        jog_pad = ctk.CTkFrame(frame, fg_color="transparent")
        jog_pad.grid(row=2, column=0, sticky="nw", padx=(20, 0), pady=(0, 6))
        jog_pad.grid_columnconfigure((0, 1, 2), weight=0, minsize=84)
        jog_pad.grid_rowconfigure((0, 1, 2), weight=0, minsize=64)

        self.window.jog_pos_y_button = ctk.CTkButton(
            jog_pad, text="+Y", command=self.window.on_jog_top, width=80, height=64
        )
        self.window.jog_pos_y_button.grid(row=0, column=1, padx=3, pady=3)

        self.window.jog_neg_x_button = ctk.CTkButton(
            jog_pad, text="-X", command=self.window.on_jog_left, width=80, height=64
        )
        self.window.jog_neg_x_button.grid(row=1, column=0, padx=3, pady=3)

        self.window.jog_pos_x_button = ctk.CTkButton(
            jog_pad, text="+X", command=self.window.on_jog_right, width=80, height=64
        )
        self.window.jog_pos_x_button.grid(row=1, column=2, padx=3, pady=3)

        self.window.jog_neg_y_button = ctk.CTkButton(
            jog_pad, text="-Y", command=self.window.on_jog_bottom, width=80, height=64
        )
        self.window.jog_neg_y_button.grid(row=2, column=1, padx=3, pady=3)

        slider_row = ctk.CTkFrame(frame, fg_color="transparent")
        slider_row.grid(row=3, column=0, sticky="ew", padx=(20, 0), pady=(0, 10))
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

        self.window._sync_jog_controls()
