from __future__ import annotations


import customtkinter as ctk


class PenTab:
    """Pen height and pen test controls."""

    def __init__(self, window, tab: ctk.CTkFrame) -> None:
        self.window = window
        self.tab = tab
        self.build()

    def build(self) -> None:
        self.tab.grid_columnconfigure(0, weight=1)
        self.tab.grid_columnconfigure(1, weight=0)

        settings = ctk.CTkFrame(self.tab, corner_radius=12)
        settings.grid(row=0, column=0, sticky="nsew", padx=(4, 4), pady=4)
        settings.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            settings,
            text="Pen Height Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(6, 4))

        self.window._build_slider_block(
            settings,
            row=1,
            label="Pen up height",
            variable=self.window.pen_up_var,
            command=self.window.on_pen_up_height_change,
            from_=0.0,
            to=10.0,
        )
        self.window._build_slider_block(
            settings,
            row=2,
            label="Pen down height",
            variable=self.window.pen_down_var,
            command=self.window.on_pen_down_height_change,
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
        info.grid(row=3, column=0, sticky="ew", padx=8, pady=(4, 6))

        tester = ctk.CTkFrame(self.tab, corner_radius=12)
        tester.grid(row=0, column=1, sticky="ns", padx=(0, 4), pady=4)
        tester.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tester,
            text="Pen Test",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(6, 4))

        ctk.CTkCheckBox(
            tester,
            text="Apply sliders live",
            variable=self.window.pen_apply_live_var,
        ).grid(row=1, column=0, sticky="w", padx=8, pady=(2, 3))

        ctk.CTkButton(
            tester,
            text="Reset defaults",
            command=self.window.on_pen_reset_defaults,
            height=34,
        ).grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 3))

        ctk.CTkButton(
            tester, text="Pen Up", command=self.window.on_pen_up, height=42
        ).grid(row=3, column=0, sticky="ew", padx=8, pady=3)
        ctk.CTkButton(
            tester, text="Pen Down", command=self.window.on_pen_down, height=42
        ).grid(row=4, column=0, sticky="ew", padx=8, pady=3)
