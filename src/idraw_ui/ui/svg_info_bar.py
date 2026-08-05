from __future__ import annotations

import customtkinter as ctk


class SvgInfoBar:
    """Top-left loaded SVG information."""

    def __init__(self, window, parent: ctk.CTkFrame) -> None:
        self.window = window
        self.parent = parent
        self.build()

    def build(self) -> None:
        ctk.CTkLabel(
            self.parent,
            textvariable=self.window.svg_var,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w")
