from __future__ import annotations

import tkinter as tk

import customtkinter as ctk


_CANVAS_WIDTH = 420
_CANVAS_HEIGHT = 360
_CANVAS_MARGIN = 18
_CANVAS_TOP_MARGIN = 36
_CANVAS_BOTTOM_MARGIN = 28


class MachineTab:
    """Machine settings tab for model selection and work-area information."""

    def __init__(self, window, tab: ctk.CTkFrame) -> None:
        self.window = window
        self.tab = tab
        self._table_canvas: tk.Canvas | None = None
        self.build()

    def build(self) -> None:
        self.tab.grid_columnconfigure(0, weight=1)
        self.tab.grid_rowconfigure(0, weight=1)

        frame = ctk.CTkFrame(self.tab, corner_radius=12)
        frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        frame.grid_columnconfigure(0, weight=0, minsize=250)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            frame,
            text="Machine Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(6, 4))

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

        ctk.CTkLabel(
            frame,
            text="Table orientation",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=3, column=0, sticky="w", padx=8, pady=(3, 2))

        ctk.CTkSegmentedButton(
            frame,
            values=["landscape", "portrait"],
            variable=self.window.table_orientation_var,
            command=self.window.on_table_orientation_change,
            width=240,
        ).grid(row=4, column=0, sticky="w", padx=8, pady=(0, 8))

        info = ctk.CTkFrame(frame, corner_radius=10)
        info.grid(row=5, column=0, sticky="new", padx=8, pady=(0, 8))
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
            wraplength=220,
        ).grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 6))

        preview = ctk.CTkFrame(frame, corner_radius=10)
        preview.grid(
            row=1, column=1, rowspan=5, sticky="nsew", padx=(0, 8), pady=(3, 8)
        )
        preview.grid_columnconfigure(0, weight=1)
        preview.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            preview,
            text="Table preview",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(6, 2))

        ctk.CTkLabel(
            preview,
            text=(
                "This drawing will be the base for choosing an alternative home corner. "
                "For now it only shows the machine footprint and the four candidate corners."
            ),
            justify="left",
            wraplength=380,
        ).grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))

        self._table_canvas = tk.Canvas(
            preview,
            width=_CANVAS_WIDTH,
            height=_CANVAS_HEIGHT,
            highlightthickness=0,
            bd=0,
            bg="#F4F7FB",
        )
        self._table_canvas.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._table_canvas.bind("<Configure>", self._on_canvas_configure)

        self.window.machine_model_var.trace_add(
            "write", self._on_machine_model_var_changed
        )
        self.window.table_orientation_var.trace_add(
            "write", self._on_machine_model_var_changed
        )
        self._redraw_table_preview()

    def _on_machine_model_var_changed(self, *_args: object) -> None:
        self._redraw_table_preview()

    def _on_canvas_configure(self, _event: tk.Event) -> None:
        self._redraw_table_preview()

    @staticmethod
    def _physical_home_corner_for_orientation(orientation: str) -> str:
        if orientation == "portrait":
            return "bottom-right"
        return "bottom-left"

    def _redraw_table_preview(self) -> None:
        if self._table_canvas is None:
            return

        model = self.window._machine_models_by_label.get(
            self.window.machine_model_var.get()
        )
        if model is None:
            return

        orientation = self.window.table_orientation_var.get().strip().lower()
        if orientation == "portrait":
            display_width_mm = model.height_mm
            display_height_mm = model.width_mm
        else:
            display_width_mm = model.width_mm
            display_height_mm = model.height_mm

        canvas = self._table_canvas
        canvas.delete("all")

        canvas_width = int(canvas.winfo_width())
        canvas_height = int(canvas.winfo_height())
        if canvas_width <= 1:
            canvas_width = _CANVAS_WIDTH
        if canvas_height <= 1:
            canvas_height = _CANVAS_HEIGHT

        available_width = canvas_width - (_CANVAS_MARGIN * 2)
        available_height = canvas_height - (_CANVAS_TOP_MARGIN + _CANVAS_BOTTOM_MARGIN)
        scale = min(
            available_width / float(display_width_mm),
            available_height / float(display_height_mm),
        )

        rect_width = display_width_mm * scale
        rect_height = display_height_mm * scale
        left = (canvas_width - rect_width) / 2.0
        top = _CANVAS_TOP_MARGIN + ((available_height - rect_height) / 2.0)
        right = left + rect_width
        bottom = top + rect_height

        canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill="#DCEBFA",
            outline="#2E6FA8",
            width=2,
            tags=("preview",),
        )

        canvas.create_text(
            canvas_width / 2.0,
            top - 12,
            text=f"{model.label} work area ({orientation})",
            fill="#29465B",
            font=("Segoe UI", 10, "bold"),
            tags=("preview",),
        )

        width_line_y = top + 18
        canvas.create_line(
            left + 10,
            width_line_y,
            right - 10,
            width_line_y,
            fill="#5A7690",
            width=1,
            tags=("preview",),
        )
        canvas.create_line(
            left + 10,
            top + 3,
            left + 10,
            width_line_y,
            fill="#5A7690",
            width=1,
            tags=("preview",),
        )
        canvas.create_line(
            right - 10,
            top + 3,
            right - 10,
            width_line_y,
            fill="#5A7690",
            width=1,
            tags=("preview",),
        )
        canvas.create_text(
            canvas_width / 2.0,
            width_line_y - 8,
            text=f"{display_width_mm} mm",
            fill="#29465B",
            font=("Segoe UI", 10),
            tags=("preview",),
        )

        height_line_x = left - 16
        canvas.create_line(
            height_line_x,
            top,
            height_line_x,
            bottom,
            fill="#5A7690",
            width=1,
            tags=("preview",),
        )
        canvas.create_line(
            height_line_x - 4,
            top,
            left - 3,
            top,
            fill="#5A7690",
            width=1,
            tags=("preview",),
        )
        canvas.create_line(
            height_line_x - 4,
            bottom,
            left - 3,
            bottom,
            fill="#5A7690",
            width=1,
            tags=("preview",),
        )
        canvas.create_text(
            height_line_x - 12,
            canvas_height / 2.0,
            text=f"{display_height_mm} mm",
            angle=90,
            fill="#29465B",
            font=("Segoe UI", 10),
            tags=("preview",),
        )

        corners = [
            (left, top, "Top left"),
            (right, top, "Top right"),
            (left, bottom, "Bottom left"),
            (right, bottom, "Bottom right"),
        ]
        physical_home_corner = self._physical_home_corner_for_orientation(orientation)
        for x, y, label in corners:
            canvas.create_oval(
                x - 5,
                y - 5,
                x + 5,
                y + 5,
                fill="#B6414B",
                outline="",
                tags=("preview",),
            )
            is_left = "left" in label.lower()
            is_top = "top" in label.lower()
            text_x = x - 10 if is_left else x
            if is_left and is_top:
                anchor = "se"
            elif is_left:
                anchor = "ne"
            elif is_top:
                anchor = "sw"
            else:
                anchor = "nw"
            text_y = y + 10 if "Bottom" in label else y - 10
            canvas.create_text(
                text_x,
                text_y,
                text=label,
                anchor=anchor,
                fill="#29465B",
                font=("Segoe UI", 9),
                tags=("preview",),
            )

            corner_key = label.lower().replace(" ", "-")
            if corner_key == physical_home_corner:
                canvas.create_oval(
                    x - 11,
                    y - 11,
                    x + 11,
                    y + 11,
                    outline="#E0A100",
                    width=3,
                    tags=("preview",),
                )
                home_label_x = x - 18 if is_left else x + 18
                home_label_y = y - 18 if is_top else y - 26
                home_anchor = (
                    "se"
                    if (is_left and is_top)
                    else ("ne" if is_left else ("sw" if is_top else "sw"))
                )
                canvas.create_text(
                    home_label_x,
                    home_label_y,
                    text="Physical home",
                    anchor=home_anchor,
                    fill="#E0A100",
                    font=("Segoe UI", 9, "bold"),
                    tags=("preview",),
                )

        bbox = canvas.bbox("preview")
        if bbox is not None:
            left_edge, top_edge, right_edge, bottom_edge = bbox
            bbox_center_x = (left_edge + right_edge) / 2.0
            bbox_center_y = (top_edge + bottom_edge) / 2.0
            target_center_x = canvas_width / 2.0
            target_center_y = canvas_height / 2.0
            canvas.move(
                "preview",
                target_center_x - bbox_center_x,
                target_center_y - bbox_center_y,
            )
