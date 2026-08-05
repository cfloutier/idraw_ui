from __future__ import annotations

import customtkinter as ctk


class ProfileBar:
    """Top-right profile controls: selector and profile creation."""

    def __init__(self, window, parent: ctk.CTkFrame) -> None:
        self.window = window
        self.parent = parent
        self.build()

    def build(self) -> None:
        self.window.profile_selector = ctk.CTkOptionMenu(
            self.parent,
            variable=self.window._profile_selector_var,
            values=self.window.settings_service.list_profile_names(),
            command=self.window.on_profile_select,
        )
        self.window.profile_selector.pack(side="left")
        self.window._sync_profile_selector(self.window.driver.plot_profile.name)

        self.window.new_profile_button = ctk.CTkButton(
            self.parent,
            text="New profile",
            width=110,
            command=self.window.on_create_profile,
        )
        self.window.new_profile_button.pack(side="left", padx=(4, 0))
