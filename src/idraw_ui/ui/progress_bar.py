from __future__ import annotations

import customtkinter as ctk


class ProgressBar(ctk.CTkProgressBar):
    """CTk progress bar with centered overlay text."""

    def __init__(
        self,
        master,
        *,
        font_size: int = 12,
        text_color: str = "white",
        **kwargs,
    ) -> None:
        super().__init__(master=master, **kwargs)
        self._progress_font = ("Arial", font_size)
        self._text_id = self._canvas.create_text(
            0,
            0,
            text="",
            fill=text_color,
            font=self._progress_font,
            anchor="c",
            tags="progress_text",
        )

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        scaled_font_size = int(self._apply_widget_scaling(self._progress_font[1]))
        self._canvas.itemconfig(
            self._text_id,
            font=(self._progress_font[0], max(8, scaled_font_size)),
        )

    def _update_dimensions_event(self, event):
        super()._update_dimensions_event(event)
        self._canvas.coords(self._text_id, event.width / 2, event.height / 2)

    def set_with_text(self, value: float, text: str) -> None:
        super().set(value)
        self._canvas.itemconfigure(self._text_id, text=text)
