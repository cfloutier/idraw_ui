from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk

from idraw_ui.backend.driver import Driver, DriverCommandResult


class AppWindow:
    """Minimal operational UI for backend machine control actions."""

    def __init__(self, driver: Driver) -> None:
        self.driver = driver
        self.title = "idraw_ui"
        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry("560x280")
        self.root.minsize(460, 240)

        self.status_var = tk.StringVar(value="Ready")
        self.state_var = tk.StringVar(value="State: idle")

        self._build_layout()

    @classmethod
    def from_profile_file(cls, path: str | Path) -> "AppWindow":
        return cls(Driver.from_profile_file(path))

    def _build_layout(self) -> None:
        frame = ttk.Frame(self.root, padding=14)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="iDraw MVP Control",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w")

        ttk.Label(frame, textvariable=self.state_var).pack(anchor="w", pady=(10, 0))

        status_box = ttk.Label(
            frame,
            textvariable=self.status_var,
            relief=tk.GROOVE,
            anchor="w",
            padding=8,
        )
        status_box.pack(fill=tk.X, pady=(6, 12))

        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X)

        ttk.Button(controls, text="Connect", command=self.on_connect).grid(
            row=0, column=0, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(controls, text="Status", command=self.on_status).grid(
            row=0, column=1, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(controls, text="Home", command=self.on_home).grid(
            row=0, column=2, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(controls, text="Pen Up", command=self.on_pen_up).grid(
            row=1, column=0, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(controls, text="Pen Down", command=self.on_pen_down).grid(
            row=1, column=1, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(controls, text="Disconnect", command=self.on_disconnect).grid(
            row=1, column=2, padx=4, pady=4, sticky="ew"
        )

        for idx in range(3):
            controls.columnconfigure(idx, weight=1)

    def _update_from_result(self, result: DriverCommandResult) -> None:
        progress = self.driver.get_progress()
        self.state_var.set(f"State: {progress.state.value}")
        if result.ok:
            self.status_var.set(f"OK: {result.message}")
        else:
            self.status_var.set(f"ERROR: {result.message}")

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
