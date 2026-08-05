from __future__ import annotations

import customtkinter as ctk


class MachineTab:
    """Machine settings tab for model selection and work-area information."""

    def __init__(self, window, tab: ctk.CTkFrame) -> None:
        self.window = window
        self.tab = tab
        self.build()

    def build(self) -> None:
        self.tab.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(self.tab, corner_radius=12)
        frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Machine Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(6, 4))

        ctk.CTkLabel(
            frame,
            text="iDraw model",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=1, column=0, sticky="w", padx=8, pady=(3, 2))

        ctk.CTkOptionMenu(
            frame,
            values=self.window.machine_model_labels,
            variable=self.window.machine_model_var,
            command=self.window.on_machine_model_change,
            width=240,
        ).grid(row=2, column=0, sticky="w", padx=8, pady=(0, 6))

        info = ctk.CTkFrame(frame, corner_radius=10)
        info.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 6))
        info.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            info,
            text="Work area",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(6, 2))

        ctk.CTkLabel(
            info,
            textvariable=self.window.machine_size_var,
            font=ctk.CTkFont(size=15),
        ).grid(row=1, column=0, sticky="w", padx=8, pady=(0, 2))

        ctk.CTkLabel(
            info,
            text=(
                "Select the physical iDraw model that matches the machine. "
                "The work area is used to keep plotting bounds consistent with the runtime."
            ),
            justify="left",
            wraplength=620,
        ).grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 6))
