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
        controls.grid(row=0, column=0, sticky="nsew", padx=(8, 10), pady=8)
        controls.grid_propagate(False)
        controls.grid_columnconfigure(0, weight=1)

        self.window.load_button = ctk.CTkButton(
            controls, text="Load SVG", command=self.window.on_load_svg, height=40
        )
        self.window.load_button.grid(
            row=0, column=0, sticky="ew", padx=12, pady=(12, 6)
        )

        self.window.reload_button = ctk.CTkButton(
            controls, text="Reload", command=self.window.on_reload_svg, height=40
        )
        self.window.reload_button.grid(row=1, column=0, sticky="ew", padx=12, pady=6)

        self.window.connect_button = ctk.CTkButton(
            controls, text="Connect", command=self.window.on_connect, height=40
        )
        self.window.connect_button.grid(
            row=2, column=0, sticky="ew", padx=12, pady=(18, 6)
        )

        nav_bar = ctk.CTkFrame(controls, fg_color="transparent")
        nav_bar.grid(row=3, column=0, sticky="ew", padx=12, pady=6)
        nav_bar.grid_columnconfigure((0, 1), weight=1)

        self.window.home_button = ctk.CTkButton(
            nav_bar, text="Home", command=self.window.on_home, height=40
        )
        self.window.home_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.window.center_button = ctk.CTkButton(
            nav_bar, text="Center", command=self.window.on_center, height=40
        )
        self.window.center_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        jog_bar = ctk.CTkFrame(controls, fg_color="transparent")
        jog_bar.grid(row=4, column=0, sticky="ew", padx=12, pady=6)
        jog_bar.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.window.jog_pos_x_button = ctk.CTkButton(
            jog_bar, text="+10x", command=self.window.on_jog_pos_x, height=36
        )
        self.window.jog_pos_x_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.window.jog_pos_y_button = ctk.CTkButton(
            jog_bar, text="+10y", command=self.window.on_jog_pos_y, height=36
        )
        self.window.jog_pos_y_button.grid(row=0, column=1, sticky="ew", padx=2)

        self.window.jog_neg_x_button = ctk.CTkButton(
            jog_bar, text="-10x", command=self.window.on_jog_neg_x, height=36
        )
        self.window.jog_neg_x_button.grid(row=0, column=2, sticky="ew", padx=2)

        self.window.jog_neg_y_button = ctk.CTkButton(
            jog_bar, text="-10y", command=self.window.on_jog_neg_y, height=36
        )
        self.window.jog_neg_y_button.grid(row=0, column=3, sticky="ew", padx=(4, 0))

        run_bar = ctk.CTkFrame(controls, fg_color="transparent")
        run_bar.grid(row=5, column=0, sticky="ew", padx=12, pady=(18, 6))
        run_bar.grid_columnconfigure((0, 1, 2), weight=1)

        self.window.play_button = ctk.CTkButton(
            run_bar, text="Play", command=self.window.on_play_pause_resume, height=52
        )
        self.window.play_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.window.pause_button = ctk.CTkButton(
            run_bar, text="Pause", command=self.window.on_pause, height=52
        )
        self.window.pause_button.grid(row=0, column=1, sticky="ew", padx=3)

        self.window.stop_button = ctk.CTkButton(
            run_bar,
            text="Stop",
            command=self.window.on_stop,
            fg_color="#B23A48",
            hover_color="#9A2F3D",
            height=52,
        )
        self.window.stop_button.grid(row=0, column=2, sticky="ew", padx=(6, 0))

        self.window.disconnect_button = ctk.CTkButton(
            controls,
            text="Disconnect",
            command=self.window.on_disconnect,
            fg_color="#4C5B73",
            hover_color="#3E4A5D",
            height=40,
        )
        self.window.disconnect_button.grid(
            row=6, column=0, sticky="ew", padx=12, pady=(18, 12)
        )

        monitor = ctk.CTkFrame(self.tab, corner_radius=12)
        monitor.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=8)
        monitor.grid_rowconfigure(3, weight=3)
        monitor.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            monitor,
            textvariable=self.window.state_var,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        self.window.status_label = ctk.CTkLabel(
            monitor,
            textvariable=self.window.status_var,
            anchor="w",
            corner_radius=8,
            fg_color=("#E8ECF2", "#2A2D35"),
            justify="left",
            height=38,
        )
        self.window.status_label.grid(
            row=1, column=0, sticky="ew", padx=14, pady=(0, 8)
        )

        ctk.CTkLabel(
            monitor,
            textvariable=self.window.metrics_var,
            anchor="w",
            justify="left",
            wraplength=700,
            font=ctk.CTkFont(size=12),
        ).grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))

        progress_frame = ctk.CTkFrame(monitor, fg_color="transparent")
        progress_frame.grid(row=3, column=0, sticky="nsew", padx=14, pady=(0, 12))
        progress_frame.grid_rowconfigure(1, weight=1)
        progress_frame.grid_columnconfigure(0, weight=1)

        progress = ctk.CTkProgressBar(progress_frame, variable=self.window.progress_var)
        progress.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        progress.set(0)

        self.window.trace_log = ctk.CTkTextbox(progress_frame, wrap="word", height=300)
        self.window.trace_log.grid(row=1, column=0, sticky="nsew")
        self.window.trace_log.insert("1.0", self.window.trace_report_var.get())
        self.window.trace_log.configure(state="disabled")
