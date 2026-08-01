from __future__ import annotations

from pathlib import Path
import tkinter as tk

import customtkinter as ctk

from idraw_ui.backend.driver import Driver, DriverCommandResult


class AppWindow:
    """Minimal operational UI for backend machine control actions."""

    def __init__(self, driver: Driver) -> None:
        self.driver = driver
        self.title = "idraw_ui"
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(self.title)
        self.root.geometry("560x280")
        self.root.minsize(460, 240)

        self.status_var = tk.StringVar(value="Ready")
        self.state_var = tk.StringVar(value="State: idle")
        self.status_label: ctk.CTkLabel | None = None

        self._build_layout()

    @classmethod
    def from_profile_file(cls, path: str | Path) -> "AppWindow":
        return cls(Driver.from_profile_file(path))

    def _build_layout(self) -> None:
        frame = ctk.CTkFrame(self.root, corner_radius=12)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="iDraw MVP Control",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            frame,
            textvariable=self.state_var,
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 6))

        self.status_label = ctk.CTkLabel(
            frame,
            textvariable=self.status_var,
            anchor="w",
            corner_radius=8,
            fg_color=("#E8ECF2", "#2A2D35"),
            justify="left",
            height=38,
        )
        self.status_label.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))

        ctk.CTkButton(controls, text="Connect", command=self.on_connect).grid(
            row=0, column=0, padx=6, pady=6, sticky="ew"
        )
        ctk.CTkButton(controls, text="Status", command=self.on_status).grid(
            row=0, column=1, padx=6, pady=6, sticky="ew"
        )
        ctk.CTkButton(controls, text="Home", command=self.on_home).grid(
            row=0, column=2, padx=6, pady=6, sticky="ew"
        )
        ctk.CTkButton(controls, text="Pen Up", command=self.on_pen_up).grid(
            row=1, column=0, padx=6, pady=6, sticky="ew"
        )
        ctk.CTkButton(controls, text="Pen Down", command=self.on_pen_down).grid(
            row=1, column=1, padx=6, pady=6, sticky="ew"
        )
        ctk.CTkButton(
            controls,
            text="Disconnect",
            command=self.on_disconnect,
            fg_color="#B23A48",
            hover_color="#9A2F3D",
        ).grid(row=1, column=2, padx=6, pady=6, sticky="ew")

        for idx in range(3):
            controls.columnconfigure(idx, weight=1)

    def _status_colors(self, ok: bool) -> tuple[str, str]:
        if ok:
            return ("#E3F8E8", "#22422B")
        return ("#FBE4E6", "#4A252B")

    def _set_status_style(self, ok: bool) -> None:
        if self.status_label is None:
            return
        light, dark = self._status_colors(ok)
        self.status_label.configure(fg_color=(light, dark))

    def _update_from_result(self, result: DriverCommandResult) -> None:
        progress = self.driver.get_progress()
        self.state_var.set(f"State: {progress.state.value}")
        if result.ok:
            self.status_var.set(f"OK: {result.message}")
            self._set_status_style(ok=True)
        else:
            self.status_var.set(f"ERROR: {result.message}")
            self._set_status_style(ok=False)

    def on_connect(self) -> None:
        self._update_from_result(self.driver.connect())

    def on_disconnect(self) -> None:
        self._update_from_result(self.driver.disconnect())

    def on_status(self) -> None:
        self._update_from_result(self.driver.status())

    def on_home(self) -> None:
        self._update_from_result(self.driver.home())

    def on_pen_up(self) -> None:
        self._update_from_result(self.driver.raise_pen())

    def on_pen_down(self) -> None:
        self._update_from_result(self.driver.lower_pen())

    def show(self) -> None:
        self.root.mainloop()
