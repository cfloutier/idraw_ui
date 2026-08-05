from __future__ import annotations

import tkinter as tk

import customtkinter as ctk


class OptionsTab:
    """Plot ordering and rendering options."""

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
            text="Plot Options",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))

        ordering = ctk.CTkOptionMenu(
            frame,
            values=[
                self.window._reordering_label(0),
                self.window._reordering_label(1),
                self.window._reordering_label(2),
                self.window._reordering_label(4),
            ],
            variable=self.window.reordering_var,
            command=self.window.on_reordering_change,
        )
        ordering.grid(row=1, column=0, sticky="w", padx=16, pady=6)

        ctk.CTkSwitch(
            frame,
            text="Auto rotate to fit the page",
            variable=self.window.auto_rotate_var,
            command=self.window.on_options_change,
        ).grid(row=2, column=0, sticky="w", padx=16, pady=6)

        ctk.CTkSwitch(
            frame,
            text="Preview mode by default",
            variable=self.window.preview_var,
            command=self.window.on_options_change,
        ).grid(row=3, column=0, sticky="w", padx=16, pady=6)

        digest_row = ctk.CTkFrame(frame, fg_color="transparent")
        digest_row.grid(row=4, column=0, sticky="w", padx=16, pady=(10, 6))
        ctk.CTkLabel(digest_row, text="Digest level").grid(
            row=0, column=0, padx=(0, 10)
        )
        digest_box = ctk.CTkComboBox(
            digest_row,
            values=["1", "2", "3"],
            variable=tk.StringVar(value=str(self.window.digest_var.get())),
            command=self.window.on_digest_change,
            width=90,
        )
        digest_box.grid(row=0, column=1)

        ctk.CTkLabel(
            frame,
            text=(
                "These options mirror the plotting knobs from the previous tool: "
                "ordering first, then orientation/preview behavior."
            ),
            justify="left",
            wraplength=600,
        ).grid(row=5, column=0, sticky="ew", padx=16, pady=(12, 14))
