from __future__ import annotations

import customtkinter as ctk

from idraw_ui.ui.profile_bar import ProfileBar
from idraw_ui.ui.svg_info_bar import SvgInfoBar


class TopBar:
    """Main window top band: SVG info on the left, profile controls on the right."""

    def __init__(self, window, parent: ctk.CTkFrame) -> None:
        self.window = window
        self.parent = parent
        self.build()

    def build(self) -> None:
        header = ctk.CTkFrame(self.parent, corner_radius=12)
        header.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        svg_info = ctk.CTkFrame(header, fg_color="transparent")
        svg_info.grid(row=0, column=0, sticky="w", padx=8, pady=(4, 2))
        SvgInfoBar(self.window, svg_info)

        profile_controls = ctk.CTkFrame(header, fg_color="transparent")
        profile_controls.grid(row=0, column=1, sticky="e", padx=8, pady=(4, 2))
        ProfileBar(self.window, profile_controls)
