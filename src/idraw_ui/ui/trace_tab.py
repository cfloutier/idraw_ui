from __future__ import annotations


import customtkinter as ctk


class TraceTab:
    """Trace tab UI for loading SVGs, running plots, and monitoring state."""

    def __init__(self, window, tab: ctk.CTkFrame) -> None:
        self.window = window
        self.tab = tab
        self.build()

    def build(self) -> None:
        self.tab.grid_columnconfigure(0, weight=0, minsize=280)
        self.tab.grid_columnconfigure(1, weight=1, minsize=420)
        self.tab.grid_rowconfigure(0, weight=1)

        controls = ctk.CTkFrame(self.tab, corner_radius=12)
        controls.configure(width=280)
        controls.grid(row=0, column=0, sticky="nsew", padx=(4, 4), pady=4)
        controls.grid_propagate(False)
        controls.grid_columnconfigure(0, weight=1)

        self.window.load_button = ctk.CTkButton(
            controls, text="Load SVG", command=self.window.on_load_svg, height=40
        )
        self.window.load_button.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 3))

        self.window.reload_button = ctk.CTkButton(
            controls, text="Reload", command=self.window.on_reload_svg, height=40
        )
        self.window.reload_button.grid(row=1, column=0, sticky="ew", padx=6, pady=3)

        run_bar = ctk.CTkFrame(controls, fg_color="transparent")
        run_bar.grid(row=2, column=0, sticky="ew", padx=6, pady=(8, 3))
        run_bar.grid_columnconfigure((0, 1, 2), weight=1)

        self.window.play_button = ctk.CTkButton(
            run_bar, text="Play", command=self.window.on_play_pause_resume, height=52
        )
        self.window.play_button.grid(row=0, column=0, sticky="ew", padx=(0, 3))

        self.window.pause_button = ctk.CTkButton(
            run_bar, text="Pause", command=self.window.on_pause, height=52
        )
        self.window.pause_button.grid(row=0, column=1, sticky="ew", padx=2)

        self.window.stop_button = ctk.CTkButton(
            run_bar,
            text="Stop",
            command=self.window.on_stop,
            fg_color="#B23A48",
            hover_color="#9A2F3D",
            height=52,
        )
        self.window.stop_button.grid(row=0, column=2, sticky="ew", padx=(3, 0))

        monitor = ctk.CTkFrame(self.tab, corner_radius=12)
        monitor.grid(row=0, column=1, sticky="nsew", padx=(0, 4), pady=4)
        monitor.grid_rowconfigure(0, weight=1)
        monitor.grid_columnconfigure(0, weight=1)

        self.window.trace_log = ctk.CTkTextbox(monitor, wrap="word", height=300)
        self.window.trace_log.grid(row=0, column=0, sticky="nsew", padx=8, pady=6)
        self.window.trace_log.insert("1.0", self.window.trace_report_var.get())
        self.window.trace_log.configure(state="disabled")
