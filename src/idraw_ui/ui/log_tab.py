from __future__ import annotations

import customtkinter as ctk


class LogTab:
    """Debug log output kept separate from operational controls."""

    def __init__(self, window, tab: ctk.CTkFrame) -> None:
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        window.trace_log = ctk.CTkTextbox(tab, wrap="word")
        window.trace_log.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        window.trace_log.insert("1.0", window.trace_report_var.get())
        window.trace_log.configure(state="disabled")
