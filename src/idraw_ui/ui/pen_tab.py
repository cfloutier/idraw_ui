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
        settings.grid(row=0, column=0, sticky="nsew", padx=(8, 10), pady=8)
        settings.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            settings,
            text="Pen Height Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        self.window._build_slider_block(
            settings,
            row=1,
            label="Pen up height",
            variable=self.window.pen_up_var,
            command=self.window.on_pen_height_change,
            from_=0.0,
            to=10.0,
        )
        self.window._build_slider_block(
            settings,
            row=2,
            label="Pen down height",
            variable=self.window.pen_down_var,
            command=self.window.on_pen_height_change,
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

        tester = ctk.CTkFrame(self.tab, corner_radius=12)
        tester.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        tester.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tester,
            text="Pen Test",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 8))

        ctk.CTkButton(
            tester, text="Pen Up", command=self.window.on_pen_up, height=42
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=6)
        ctk.CTkButton(
            tester, text="Pen Down", command=self.window.on_pen_down, height=42
        ).grid(row=2, column=0, sticky="ew", padx=14, pady=6)
        ctk.CTkButton(
            tester,
            text="Connect",
            command=self.window.on_connect,
            fg_color="#4C5B73",
            hover_color="#3E4A5D",
            height=40,
        ).grid(row=3, column=0, sticky="ew", padx=14, pady=(18, 14))
