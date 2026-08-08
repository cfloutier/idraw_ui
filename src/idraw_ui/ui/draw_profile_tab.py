from __future__ import annotations

import customtkinter as ctk


class DrawProfileTab:
    """Combined speed, pen height, and pen test controls."""

    def __init__(self, window, tab: ctk.CTkFrame) -> None:
        self.window = window
        self.tab = tab
        self.build()

    def build(self) -> None:
        self.tab.grid_columnconfigure(0, weight=1, uniform="half")
        self.tab.grid_columnconfigure(1, weight=1, uniform="half")
        self.tab.grid_rowconfigure(0, weight=1)

        # ── left: speed settings ─────────────────────────────────────────────
        speed_frame = ctk.CTkFrame(self.tab, corner_radius=12)
        speed_frame.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=4)
        speed_frame.grid_columnconfigure(0, weight=1)

        speed_header = ctk.CTkFrame(speed_frame, fg_color="transparent")
        speed_header.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 4))
        speed_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            speed_header,
            text="Speed",
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

        # ── right: pen height + test ─────────────────────────────────────────
        pen_frame = ctk.CTkFrame(self.tab, corner_radius=12)
        pen_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 4), pady=4)
        pen_frame.grid_columnconfigure(0, weight=1)
        pen_frame.grid_columnconfigure(1, weight=0)

        pen_header = ctk.CTkFrame(pen_frame, fg_color="transparent")
        pen_header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(6, 4))
        pen_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            pen_header,
            text="Pen Height",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            pen_header,
            text="Reset defaults",
            command=self.window.on_pen_reset_defaults,
            height=32,
        ).grid(row=0, column=1, sticky="e")

        self.window._build_slider_block(
            pen_frame,
            row=1,
            label="Pen up height",
            variable=self.window.pen_up_var,
            command=self.window.on_pen_up_height_change,
            from_=0.0,
            to=10.0,
        )
        self.window._build_slider_block(
            pen_frame,
            row=2,
            label="Pen down height",
            variable=self.window.pen_down_var,
            command=self.window.on_pen_down_height_change,
            from_=0.0,
            to=10.0,
        )

        actions = ctk.CTkFrame(pen_frame, fg_color="transparent")
        actions.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=(8, 6))
        actions.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkCheckBox(
            actions,
            text="Apply live",
            variable=self.window.pen_apply_live_var,
        ).grid(row=0, column=0, sticky="w", padx=(0, 4))

        ctk.CTkButton(
            actions,
            text="Pen Up",
            command=self.window.on_pen_up,
            height=42,
        ).grid(row=0, column=1, sticky="ew", padx=4)

        ctk.CTkButton(
            actions,
            text="Pen Down",
            command=self.window.on_pen_down,
            height=42,
        ).grid(row=0, column=2, sticky="ew", padx=(4, 0))
