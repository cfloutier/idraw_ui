from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from idraw_ui.backend.machine_models import (
    MACHINE_HOME_CORNERS,
    MachineModelDefinition,
    display_axis_vectors,
    display_home_corner,
)
from idraw_ui.ui.tools import format_distance_mm

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
        frame.grid_rowconfigure(11, weight=1)

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

        ctk.CTkLabel(
            frame,
            text=(
                "Orientation = how the plotter is physically placed on the table. "
                "This is a practical choice and it defines Jog directions."
            ),
            justify="left",
            wraplength=220,
        ).grid(row=5, column=0, sticky="ew", padx=8, pady=(0, 8))

        ctk.CTkLabel(
            frame,
            text="My home",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=6, column=0, sticky="w", padx=8, pady=(3, 2))

        ctk.CTkOptionMenu(
            frame,
            values=list(MACHINE_HOME_CORNERS),
            variable=self.window.machine_home_corner_var,
            command=self.window.on_machine_home_corner_change,
            width=240,
        ).grid(row=7, column=0, sticky="w", padx=8, pady=(0, 6))

        padding_box = ctk.CTkFrame(frame, fg_color="transparent")
        padding_box.grid(row=8, column=0, sticky="ew", padx=8, pady=(0, 8))
        padding_box.grid_columnconfigure(0, weight=1)
        padding_box.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            padding_box,
            text="Padding",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        padding_value_var = tk.StringVar(
            value=format_distance_mm(self.window.machine_home_padding_var.get())
        )

        def on_padding_change(value: float) -> None:
            padding_value_var.set(format_distance_mm(value))
            self.window.on_machine_home_padding_change(value)

        ctk.CTkLabel(
            padding_box,
            textvariable=padding_value_var,
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=1, sticky="e")

        ctk.CTkSlider(
            padding_box,
            from_=0.0,
            to=50.0,
            variable=self.window.machine_home_padding_var,
            command=on_padding_change,
            number_of_steps=50,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))

        home_actions = ctk.CTkFrame(frame, fg_color="transparent")
        home_actions.grid(row=9, column=0, sticky="ew", padx=8, pady=(0, 8))
        home_actions.grid_columnconfigure((0, 1), weight=1)

        self.window.machine_physical_home_button = ctk.CTkButton(
            home_actions,
            text="Physical Home",
            command=self.window.on_machine_physical_home,
            height=40,
        )
        self.window.machine_physical_home_button.grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )

        self.window.machine_my_home_button = ctk.CTkButton(
            home_actions,
            text="My home",
            command=self.window.on_machine_my_home,
            height=40,
        )
        self.window.machine_my_home_button.grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )

        info = ctk.CTkFrame(frame, corner_radius=10)
        info.grid(row=10, column=0, sticky="new", padx=8, pady=(0, 8))
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
            row=1, column=1, rowspan=10, sticky="nsew", padx=(0, 8), pady=(16, 8)
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
        self.window.machine_home_corner_var.trace_add(
            "write", self._on_machine_model_var_changed
        )
        self.window.machine_home_padding_var.trace_add(
            "write", self._on_machine_model_var_changed
        )
        self._redraw_table_preview()

    def _on_machine_model_var_changed(self, *_args: object) -> None:
        self._redraw_table_preview()

    def _on_canvas_configure(self, _event: tk.Event) -> None:
        self._redraw_table_preview()

    @staticmethod
    def _display_axis_vectors(
        model: MachineModelDefinition,
        display_orientation: str,
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        return display_axis_vectors(model, display_orientation)

    @staticmethod
    def _physical_home_corner_for_display(
        model: MachineModelDefinition,
        display_orientation: str,
    ) -> str:
        return display_home_corner(model, display_orientation)

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
        physical_home_corner = self._physical_home_corner_for_display(
            model, orientation
        )
        selected_home_corner = self.window.machine_home_corner_var.get().strip().lower()
        padding_mm = max(0.0, float(self.window.machine_home_padding_var.get()))
        safe_inset = min(
            padding_mm * scale,
            max(0.0, rect_width / 2.0 - 6),
            max(0.0, rect_height / 2.0 - 6),
        )
        if safe_inset > 0.0:
            canvas.create_rectangle(
                left + safe_inset,
                top + safe_inset,
                right - safe_inset,
                bottom - safe_inset,
                outline="#3A7BD5",
                width=1,
                dash=(4, 3),
                tags=("preview",),
            )
            canvas.create_text(
                left + safe_inset + 10,
                top + safe_inset + 10,
                text=f"Padding {format_distance_mm(padding_mm)}",
                anchor="nw",
                fill="#3A7BD5",
                font=("Segoe UI", 9, "bold"),
                tags=("preview",),
            )
        x_axis_dir, y_axis_dir = self._display_axis_vectors(model, orientation)
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
                    "se" if (is_left and is_top) else ("ne" if is_left else "sw")
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

            if corner_key == selected_home_corner:
                marker_x = left + safe_inset if is_left else right - safe_inset
                marker_y = top + safe_inset if is_top else bottom - safe_inset
                canvas.create_oval(
                    marker_x - 11,
                    marker_y - 11,
                    marker_x + 11,
                    marker_y + 11,
                    outline="#3A7BD5",
                    width=3,
                    tags=("preview",),
                )
                my_home_label_x = marker_x + 18 if is_left else marker_x - 18
                my_home_label_y = marker_y + 18 if is_top else marker_y - 18
                my_home_anchor = (
                    "sw"
                    if (is_left and is_top)
                    else ("se" if is_top else ("nw" if is_left else "ne"))
                )
                canvas.create_text(
                    my_home_label_x,
                    my_home_label_y,
                    text="My home",
                    anchor=my_home_anchor,
                    fill="#3A7BD5",
                    font=("Segoe UI", 9, "bold"),
                    tags=("preview",),
                )

        axis_origin_x = (left + right) / 2.0
        axis_origin_y = (top + bottom) / 2.0
        axis_length = 32

        x_end_x = axis_origin_x + (x_axis_dir[0] * axis_length)
        x_end_y = axis_origin_y + (x_axis_dir[1] * axis_length)
        y_end_x = axis_origin_x + (y_axis_dir[0] * axis_length)
        y_end_y = axis_origin_y + (y_axis_dir[1] * axis_length)

        canvas.create_line(
            axis_origin_x,
            axis_origin_y,
            x_end_x,
            x_end_y,
            fill="#2E7D32",
            width=2,
            arrow="last",
            tags=("preview",),
        )
        canvas.create_text(
            x_end_x + (x_axis_dir[0] * 10),
            x_end_y + (x_axis_dir[1] * 10),
            text="X+",
            fill="#2E7D32",
            font=("Segoe UI", 9, "bold"),
            tags=("preview",),
        )

        canvas.create_line(
            axis_origin_x,
            axis_origin_y,
            y_end_x,
            y_end_y,
            fill="#8E5EA2",
            width=2,
            arrow="last",
            tags=("preview",),
        )
        canvas.create_text(
            y_end_x + (y_axis_dir[0] * 10),
            y_end_y + (y_axis_dir[1] * 10),
            text="Y+",
            fill="#8E5EA2",
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
