from __future__ import annotations

import customtkinter as ctk


class SvgInfoBar:
    """Top-left SVG and plotting status information."""

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

        ctk.CTkLabel(
            self.parent,
            textvariable=self.window.state_var,
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            self.parent,
            textvariable=self.window.metrics_var,
            font=ctk.CTkFont(size=12),
            justify="left",
        ).pack(anchor="w", pady=(2, 0))
