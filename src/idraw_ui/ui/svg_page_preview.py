from __future__ import annotations

import math
import re
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

import customtkinter as ctk

_LENGTH_PATTERN = re.compile(
    r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*([a-zA-Z]*)\s*$"
)
_NUMBER_PATTERN = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")
_MM_PER_UNIT = {
    "": 25.4 / 96.0,
    "px": 25.4 / 96.0,
    "mm": 1.0,
    "cm": 10.0,
    "in": 25.4,
    "pt": 25.4 / 72.0,
    "pc": 25.4 / 6.0,
}


@dataclass(frozen=True)
class SvgPageSize:
    width: float
    height: float
    label: str


@dataclass(frozen=True)
class BBoxMm:
    """Bounding box of the actual drawing content, in page-relative mm."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y


@dataclass(frozen=True)
class PagePlacement:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def fits_table(self) -> bool:
        return self.left >= 0 and self.top >= 0

    def fits_within(
        self,
        table_width: float,
        table_height: float,
        *,
        margin_top: float = 0.0,
        margin_bottom: float = 0.0,
        margin_left: float = 0.0,
        margin_right: float = 0.0,
    ) -> bool:
        return (
            self.left >= margin_left
            and self.top >= margin_top
            and self.right <= table_width - margin_right
            and self.bottom <= table_height - margin_bottom
        )


def calculate_page_placement(
    *,
    table_width: float,
    table_height: float,
    page_width: float,
    page_height: float,
    home_corner: str,
    margin_top: float,
    margin_bottom: float,
    margin_left: float,
    margin_right: float,
) -> PagePlacement:
    margin_top = max(0.0, margin_top)
    margin_bottom = max(0.0, margin_bottom)
    margin_left = max(0.0, margin_left)
    margin_right = max(0.0, margin_right)
    if "left" in home_corner:
        left = margin_left
    elif "right" in home_corner:
        left = table_width - margin_right - page_width
    else:
        raise ValueError(f"Invalid home corner: {home_corner}")

    if "top" in home_corner:
        top = margin_top
    elif "bottom" in home_corner:
        top = table_height - margin_bottom - page_height
    else:
        raise ValueError(f"Invalid home corner: {home_corner}")

    return PagePlacement(
        left=left,
        top=top,
        right=left + page_width,
        bottom=top + page_height,
    )


def _parse_length(value: str | None) -> tuple[float, str] | None:
    if value is None:
        return None
    match = _LENGTH_PATTERN.fullmatch(value)
    if match is None:
        return None
    unit = match.group(2).lower()
    if unit not in _MM_PER_UNIT:
        return None
    return float(match.group(1)), unit


def _parse_length_mm(value: str | None) -> float | None:
    parsed = _parse_length(value)
    if parsed is None:
        return None
    number, unit = parsed
    length_mm = number * _MM_PER_UNIT[unit]
    return length_mm if length_mm > 0 else None


def _parse_view_box(value: str | None) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    try:
        values = [float(part) for part in re.split(r"[\s,]+", value.strip())]
    except ValueError:
        return None
    if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
        return None
    return values[0], values[1], values[2], values[3]


def read_svg_page_size(path: str | Path) -> SvgPageSize:
    root = ET.parse(str(path)).getroot()
    width_mm = _parse_length_mm(root.get("width"))
    height_mm = _parse_length_mm(root.get("height"))
    view_box = _parse_view_box(root.get("viewBox"))

    if width_mm is not None and height_mm is not None:
        return SvgPageSize(width_mm, height_mm, "mm")

    if view_box is not None:
        _view_min_x, _view_min_y, view_width, view_height = view_box
        if width_mm is not None:
            return SvgPageSize(
                width_mm,
                width_mm * view_height / view_width,
                "mm",
            )
        if height_mm is not None:
            return SvgPageSize(
                height_mm * view_width / view_height,
                height_mm,
                "mm",
            )
        return SvgPageSize(view_width, view_height, "SVG units")

    raise ValueError("SVG has no usable page dimensions")


# --- Drawing bounding box -------------------------------------------------
#
# The goal is only to show the reader how big the actual drawing is inside
# the page, not to render it. So we never rasterize/trace the SVG: we just
# walk the element tree, apply the accumulated transform of each element to
# its defining coordinates (path/rect/circle/... control points), and keep
# a running min/max. For curves (C/S/Q/T) this uses the control points
# rather than the flattened curve, which is a safe over-estimate (a Bezier
# curve always stays within the convex hull of its control points).

_Matrix = tuple[float, float, float, float, float, float]
_IDENTITY: _Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
_TRANSFORM_FUNC_PATTERN = re.compile(r"([a-zA-Z]+)\s*\(([^)]*)\)")

_CONTAINER_TAGS = {"svg", "g", "a", "switch"}
_SKIP_TAGS = {
    "defs",
    "symbol",
    "clipPath",
    "mask",
    "pattern",
    "metadata",
    "style",
    "title",
    "desc",
    "namedview",
}

_PATH_TOKEN_PATTERN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|" + _NUMBER_PATTERN.pattern)
_PATH_ARG_COUNTS = {
    "M": 2,
    "L": 2,
    "T": 2,
    "H": 1,
    "V": 1,
    "S": 4,
    "Q": 4,
    "C": 6,
    "A": 7,
    "Z": 0,
}


def _mat_mul(m1: _Matrix, m2: _Matrix) -> _Matrix:
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def _apply_matrix(matrix: _Matrix, x: float, y: float) -> tuple[float, float]:
    a, b, c, d, e, f = matrix
    return a * x + c * y + e, b * x + d * y + f


def _parse_transform(value: str | None) -> _Matrix:
    matrix = _IDENTITY
    if not value:
        return matrix
    for name, args_str in _TRANSFORM_FUNC_PATTERN.findall(value):
        args = [float(v) for v in _NUMBER_PATTERN.findall(args_str)]
        if not args:
            continue
        name = name.lower()
        local: _Matrix | None = None
        if name == "translate":
            tx = args[0]
            ty = args[1] if len(args) > 1 else 0.0
            local = (1.0, 0.0, 0.0, 1.0, tx, ty)
        elif name == "scale":
            sx = args[0]
            sy = args[1] if len(args) > 1 else sx
            local = (sx, 0.0, 0.0, sy, 0.0, 0.0)
        elif name == "rotate":
            angle = math.radians(args[0])
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            rotation: _Matrix = (cos_a, sin_a, -sin_a, cos_a, 0.0, 0.0)
            if len(args) >= 3:
                cx, cy = args[1], args[2]
                local = _mat_mul(
                    _mat_mul((1.0, 0.0, 0.0, 1.0, cx, cy), rotation),
                    (1.0, 0.0, 0.0, 1.0, -cx, -cy),
                )
            else:
                local = rotation
        elif name == "matrix" and len(args) == 6:
            local = (args[0], args[1], args[2], args[3], args[4], args[5])
        elif name == "skewx":
            local = (1.0, 0.0, math.tan(math.radians(args[0])), 1.0, 0.0, 0.0)
        elif name == "skewy":
            local = (1.0, math.tan(math.radians(args[0])), 0.0, 1.0, 0.0, 0.0)
        if local is not None:
            matrix = _mat_mul(matrix, local)
    return matrix


def _iter_path_points(d: str) -> list[tuple[float, float]]:
    tokens = _PATH_TOKEN_PATTERN.findall(d)
    points: list[tuple[float, float]] = []
    index = 0
    cur_x = cur_y = 0.0
    start_x = start_y = 0.0
    command = ""

    def read_floats(count: int) -> list[float]:
        nonlocal index
        values = [float(tok) for tok in tokens[index : index + count]]
        index += count
        return values

    while index < len(tokens):
        token = tokens[index]
        if token.isalpha():
            command = token
            index += 1
        elif not command:
            break

        upper = command.upper()
        relative = command.islower()

        if upper == "Z":
            cur_x, cur_y = start_x, start_y
            points.append((cur_x, cur_y))
            command = ""
            continue

        needed = _PATH_ARG_COUNTS.get(upper)
        if needed is None or index + needed > len(tokens):
            break
        values = read_floats(needed)

        if upper == "M":
            x, y = values
            if relative:
                x += cur_x
                y += cur_y
            cur_x, cur_y = x, y
            start_x, start_y = x, y
            points.append((x, y))
            command = "l" if relative else "L"
        elif upper in ("L", "T"):
            x, y = values
            if relative:
                x += cur_x
                y += cur_y
            cur_x, cur_y = x, y
            points.append((x, y))
        elif upper == "H":
            x = values[0]
            if relative:
                x += cur_x
            cur_x = x
            points.append((cur_x, cur_y))
        elif upper == "V":
            y = values[0]
            if relative:
                y += cur_y
            cur_y = y
            points.append((cur_x, cur_y))
        elif upper == "C":
            x1, y1, x2, y2, x, y = values
            if relative:
                x1 += cur_x
                y1 += cur_y
                x2 += cur_x
                y2 += cur_y
                x += cur_x
                y += cur_y
            points.append((x1, y1))
            points.append((x2, y2))
            points.append((x, y))
            cur_x, cur_y = x, y
        elif upper == "S":
            x2, y2, x, y = values
            if relative:
                x2 += cur_x
                y2 += cur_y
                x += cur_x
                y += cur_y
            points.append((x2, y2))
            points.append((x, y))
            cur_x, cur_y = x, y
        elif upper == "Q":
            x1, y1, x, y = values
            if relative:
                x1 += cur_x
                y1 += cur_y
                x += cur_x
                y += cur_y
            points.append((x1, y1))
            points.append((x, y))
            cur_x, cur_y = x, y
        elif upper == "A":
            *_ignored, x, y = values
            if relative:
                x += cur_x
                y += cur_y
            # Arc extremes are approximated by its endpoint only.
            points.append((x, y))
            cur_x, cur_y = x, y

    return points


def _num(elem: ET.Element, name: str, default: float = 0.0) -> float:
    value = elem.get(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _rect_points(elem: ET.Element) -> list[tuple[float, float]]:
    x, y = _num(elem, "x"), _num(elem, "y")
    w, h = _num(elem, "width"), _num(elem, "height")
    if w <= 0 or h <= 0:
        return []
    return [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]


def _ellipse_sample(
    cx: float, cy: float, rx: float, ry: float, steps: int = 32
) -> list[tuple[float, float]]:
    return [
        (
            cx + rx * math.cos(2 * math.pi * i / steps),
            cy + ry * math.sin(2 * math.pi * i / steps),
        )
        for i in range(steps)
    ]


def _circle_points(elem: ET.Element) -> list[tuple[float, float]]:
    r = _num(elem, "r")
    if r <= 0:
        return []
    return _ellipse_sample(_num(elem, "cx"), _num(elem, "cy"), r, r)


def _ellipse_points(elem: ET.Element) -> list[tuple[float, float]]:
    rx, ry = _num(elem, "rx"), _num(elem, "ry")
    if rx <= 0 or ry <= 0:
        return []
    return _ellipse_sample(_num(elem, "cx"), _num(elem, "cy"), rx, ry)


def _line_points(elem: ET.Element) -> list[tuple[float, float]]:
    return [
        (_num(elem, "x1"), _num(elem, "y1")),
        (_num(elem, "x2"), _num(elem, "y2")),
    ]


def _poly_points(elem: ET.Element) -> list[tuple[float, float]]:
    raw = elem.get("points")
    if not raw:
        return []
    numbers = [float(v) for v in _NUMBER_PATTERN.findall(raw)]
    return list(zip(numbers[0::2], numbers[1::2]))


_LEAF_POINT_READERS: dict[str, Callable[[ET.Element], list[tuple[float, float]]]] = {
    "path": lambda elem: _iter_path_points(elem.get("d") or ""),
    "rect": _rect_points,
    "circle": _circle_points,
    "ellipse": _ellipse_points,
    "line": _line_points,
    "polyline": _poly_points,
    "polygon": _poly_points,
}


def _is_hidden(elem: ET.Element) -> bool:
    declarations: dict[str, str] = {}
    for part in (elem.get("style") or "").split(";"):
        key, sep, value = part.partition(":")
        if sep:
            declarations[key.strip().lower()] = value.strip().lower()
    display = declarations.get("display", (elem.get("display") or "").strip().lower())
    visibility = declarations.get(
        "visibility", (elem.get("visibility") or "").strip().lower()
    )
    return display == "none" or visibility == "hidden"


def _collect_points_mm(
    root: ET.Element,
    scale_x: float,
    scale_y: float,
    origin_x: float,
    origin_y: float,
) -> BBoxMm | None:
    min_x = min_y = math.inf
    max_x = max_y = -math.inf
    found = False

    def visit(elem: ET.Element, matrix: _Matrix) -> None:
        nonlocal min_x, min_y, max_x, max_y, found
        tag = elem.tag.split("}")[-1]
        if tag in _SKIP_TAGS or _is_hidden(elem):
            return
        combined = _mat_mul(matrix, _parse_transform(elem.get("transform")))
        if tag in _CONTAINER_TAGS:
            for child in elem:
                visit(child, combined)
            return
        reader = _LEAF_POINT_READERS.get(tag)
        if reader is None:
            return
        for x, y in reader(elem):
            tx, ty = _apply_matrix(combined, x, y)
            min_x = min(min_x, tx)
            max_x = max(max_x, tx)
            min_y = min(min_y, ty)
            max_y = max(max_y, ty)
            found = True

    visit(root, _IDENTITY)
    if not found:
        return None
    return BBoxMm(
        (min_x - origin_x) * scale_x,
        (min_y - origin_y) * scale_y,
        (max_x - origin_x) * scale_x,
        (max_y - origin_y) * scale_y,
    )


def read_svg_drawing_bbox(path: str | Path) -> BBoxMm | None:
    """Bounding box of the drawn content, in mm relative to the page origin.

    Returns None when the physical page scale is unknown (no mm/in/... width
    on the root SVG) or when no drawable geometry was found.
    """
    try:
        root = ET.parse(str(path)).getroot()
    except (ET.ParseError, OSError):
        return None

    view_box = _parse_view_box(root.get("viewBox"))
    width_len = _parse_length(root.get("width"))
    height_len = _parse_length(root.get("height"))

    if view_box is not None:
        origin_x, origin_y, vb_width, vb_height = view_box
        scale_x = (
            width_len[0] * _MM_PER_UNIT[width_len[1]] / vb_width
            if width_len is not None and vb_width
            else None
        )
        scale_y = (
            height_len[0] * _MM_PER_UNIT[height_len[1]] / vb_height
            if height_len is not None and vb_height
            else None
        )
        if scale_x is None and scale_y is None:
            return None
        scale_x = scale_x if scale_x is not None else scale_y
        scale_y = scale_y if scale_y is not None else scale_x
    else:
        if width_len is None:
            return None
        scale_x = scale_y = _MM_PER_UNIT[width_len[1]]
        origin_x = origin_y = 0.0

    assert scale_x is not None and scale_y is not None
    return _collect_points_mm(root, scale_x, scale_y, origin_x, origin_y)


def _format_size_value(value: float) -> str:
    rounded = round(value)
    if abs(value - rounded) < 0.05:
        return str(rounded)
    return f"{value:.1f}"


class SvgPagePreview:
    """Responsive preview of the loaded SVG page placed on the plotter table."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        *,
        on_fit_changed: Callable[[bool | None], None] | None = None,
    ) -> None:
        self._path: Path | None = None
        self._page_size: SvgPageSize | None = None
        self._drawing_bbox: BBoxMm | None = None
        self._table_width = 1.0
        self._table_height = 1.0
        self._home_corner = "top-left"
        self._margin_top = 0.0
        self._margin_bottom = 0.0
        self._margin_left = 0.0
        self._margin_right = 0.0
        self._on_fit_changed = on_fit_changed
        self._last_fit_state: bool | None = None

        self.frame = ctk.CTkFrame(parent, corner_radius=12)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(
            self.frame,
            bg="#F7F9FC",
            highlightthickness=0,
        )
        self._canvas.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self._canvas.bind("<Configure>", self._on_configure)
        self._redraw()

    def grid(self, **kwargs: object) -> None:
        self.frame.grid(**kwargs)

    def set_svg(self, path: str | Path) -> None:
        self._path = Path(path)
        try:
            self._page_size = read_svg_page_size(self._path)
        except (ET.ParseError, OSError, ValueError):
            self._page_size = None
        self._drawing_bbox = read_svg_drawing_bbox(self._path)
        self._redraw()
        self._notify_fit_changed()

    def get_drawing_bbox(self) -> BBoxMm | None:
        return self._drawing_bbox

    def set_table(
        self,
        *,
        width_mm: float,
        height_mm: float,
        home_corner: str,
        margin_top_mm: float,
        margin_bottom_mm: float,
        margin_left_mm: float,
        margin_right_mm: float,
    ) -> None:
        self._table_width = max(1.0, float(width_mm))
        self._table_height = max(1.0, float(height_mm))
        self._home_corner = home_corner
        self._margin_top = max(0.0, float(margin_top_mm))
        self._margin_bottom = max(0.0, float(margin_bottom_mm))
        self._margin_left = max(0.0, float(margin_left_mm))
        self._margin_right = max(0.0, float(margin_right_mm))
        self._redraw()
        self._notify_fit_changed()

    def page_fits_table(self) -> bool | None:
        page = self._page_size
        if page is None or page.label != "mm":
            return None
        placement = calculate_page_placement(
            table_width=self._table_width,
            table_height=self._table_height,
            page_width=page.width,
            page_height=page.height,
            home_corner=self._home_corner,
            margin_top=self._margin_top,
            margin_bottom=self._margin_bottom,
            margin_left=self._margin_left,
            margin_right=self._margin_right,
        )
        return placement.fits_within(
            self._table_width,
            self._table_height,
            margin_top=self._margin_top,
            margin_bottom=self._margin_bottom,
            margin_left=self._margin_left,
            margin_right=self._margin_right,
        )

    def _notify_fit_changed(self) -> None:
        fit_state = self.page_fits_table()
        if fit_state == self._last_fit_state:
            return
        self._last_fit_state = fit_state
        if self._on_fit_changed is not None:
            self._on_fit_changed(fit_state)

    def _on_configure(self, _event: tk.Event) -> None:
        self._redraw()

    def _redraw(self) -> None:
        canvas = self._canvas
        canvas.delete("all")
        width = max(1, int(canvas.winfo_width()))
        height = max(1, int(canvas.winfo_height()))

        if self._path is None:
            canvas.create_text(
                width / 2,
                height / 2,
                text="No SVG loaded",
                fill="#647786",
                font=("Segoe UI", 12, "bold"),
            )
            return

        if self._page_size is None:
            canvas.create_text(
                width / 2,
                height / 2,
                text=f"{self._path.name}\nPage size unavailable",
                justify="center",
                fill="#8A4B52",
                font=("Segoe UI", 11, "bold"),
            )
            return

        page = self._page_size
        canvas.create_text(
            width / 2,
            18,
            text=self._path.name,
            fill="#29465B",
            font=("Segoe UI", 11, "bold"),
        )

        side_margin = 30.0
        top_margin = 58.0
        bottom_margin = 56.0
        available_width = max(1.0, width - (side_margin * 2))
        available_height = max(1.0, height - top_margin - bottom_margin)
        scale = min(
            available_width / self._table_width,
            available_height / self._table_height,
        )
        table_pixel_width = self._table_width * scale
        table_pixel_height = self._table_height * scale
        table_left = (width - table_pixel_width) / 2.0
        table_top = top_margin + ((available_height - table_pixel_height) / 2.0)
        table_right = table_left + table_pixel_width
        table_bottom = table_top + table_pixel_height

        canvas.create_rectangle(
            table_left,
            table_top,
            table_right,
            table_bottom,
            fill="#E8EDF2",
            outline="#526776",
            width=2,
        )

        safe_left = table_left + (self._margin_left * scale)
        safe_top = table_top + (self._margin_top * scale)
        safe_right = table_right - (self._margin_right * scale)
        safe_bottom = table_bottom - (self._margin_bottom * scale)
        safe_area_valid = safe_left < safe_right and safe_top < safe_bottom
        canvas.create_rectangle(
            safe_left,
            safe_top,
            safe_right,
            safe_bottom,
            outline="#3A7BD5" if safe_area_valid else "#B42318",
            width=2,
            dash=(5, 3),
        )

        placement_page_width = page.width
        placement_page_height = page.height
        physical_size_known = page.label == "mm"
        if not physical_size_known:
            preview_long_side = max(self._table_width, self._table_height) * 0.28
            page_long_side = max(page.width, page.height)
            placement_page_width = page.width * preview_long_side / page_long_side
            placement_page_height = page.height * preview_long_side / page_long_side

        placement = calculate_page_placement(
            table_width=self._table_width,
            table_height=self._table_height,
            page_width=placement_page_width,
            page_height=placement_page_height,
            home_corner=self._home_corner,
            margin_top=self._margin_top,
            margin_bottom=self._margin_bottom,
            margin_left=self._margin_left,
            margin_right=self._margin_right,
        )
        left = table_left + (placement.left * scale)
        top = table_top + (placement.top * scale)
        right = table_left + (placement.right * scale)
        bottom = table_top + (placement.bottom * scale)
        page_fits = placement.fits_within(
            self._table_width,
            self._table_height,
            margin_top=self._margin_top,
            margin_bottom=self._margin_bottom,
            margin_left=self._margin_left,
            margin_right=self._margin_right,
        )

        canvas.create_rectangle(
            left + 3,
            top + 4,
            right + 3,
            bottom + 4,
            fill="#C7D0D8",
            outline="",
        )
        canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill="#FFFFFF",
            outline="#2E6FA8" if page_fits else "#B42318",
            width=3,
        )

        drawing_bbox = self._drawing_bbox if physical_size_known else None
        if drawing_bbox is not None:
            bbox_left = left + (drawing_bbox.min_x * scale)
            bbox_top = top + (drawing_bbox.min_y * scale)
            bbox_right = left + (drawing_bbox.max_x * scale)
            bbox_bottom = top + (drawing_bbox.max_y * scale)
            # White halo drawn under the dashed outline so the bbox stays
            # legible even when it coincides with the page border or other
            # lines in the artwork (e.g. a drawing that traces its own
            # page frame, as in the A6 test SVG).
            canvas.create_rectangle(
                bbox_left,
                bbox_top,
                bbox_right,
                bbox_bottom,
                outline="#FFFFFF",
                width=5,
            )
            canvas.create_rectangle(
                bbox_left,
                bbox_top,
                bbox_right,
                bbox_bottom,
                outline="#C2185B",
                width=2,
                dash=(3, 2),
            )

        # "Up" direction arrow — disabled (kept for easy re-enabling), it was
        # only useful while debugging table/home orientation.
        # arrow_x = (left + right) / 2.0
        # page_pixel_height = bottom - top
        # arrow_top = top + (page_pixel_height * 0.22)
        # arrow_bottom = top + (page_pixel_height * 0.66)
        # canvas.create_line(
        #     arrow_x,
        #     arrow_bottom,
        #     arrow_x,
        #     arrow_top,
        #     arrow="last",
        #     arrowshape=(12, 15, 6),
        #     fill="#E16B2D",
        #     width=4,
        # )
        # canvas.create_text(
        #     arrow_x,
        #     min(bottom - 9, arrow_bottom + 12),
        #     text="Up",
        #     fill="#B94F1C",
        #     font=("Segoe UI", 10, "bold"),
        # )

        size_text = (
            f"{_format_size_value(page.width)} × "
            f"{_format_size_value(page.height)} {page.label}"
        )
        if drawing_bbox is not None:
            size_text += (
                f"  ·  drawing {_format_size_value(drawing_bbox.width)} × "
                f"{_format_size_value(drawing_bbox.height)} mm"
            )
        home_points = {
            "top-left": (safe_left, safe_top),
            "top-right": (safe_right, safe_top),
            "bottom-left": (safe_left, safe_bottom),
            "bottom-right": (safe_right, safe_bottom),
        }
        home_x, home_y = home_points[self._home_corner]
        canvas.create_oval(
            home_x - 7,
            home_y - 7,
            home_x + 7,
            home_y + 7,
            fill="#E16B2D",
            outline="#FFFFFF",
            width=2,
        )
        canvas.create_text(
            width / 2,
            39,
            text=f"Home: {self._home_corner}",
            fill="#B94F1C",
            font=("Segoe UI", 10, "bold"),
        )
        canvas.create_text(
            width / 2,
            height - 24,
            text=(
                size_text
                if physical_size_known
                else f"{size_text} · physical scale unavailable"
            ),
            fill="#29465B" if page_fits else "#B42318",
            font=("Segoe UI", 11, "bold"),
        )
