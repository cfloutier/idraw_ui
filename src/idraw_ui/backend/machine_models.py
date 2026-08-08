from __future__ import annotations

from dataclasses import dataclass

MACHINE_HOME_CORNERS = (
    "top-left",
    "top-right",
    "bottom-right",
    "bottom-left",
)


@dataclass(frozen=True)
class MachineModelDefinition:
    key: str
    label: str
    runtime_model: int
    width_mm: int
    height_mm: int
    physical_home: str
    my_home_corner: str
    long_axis_is_y: bool
    x_axis_toward_home: bool
    y_axis_toward_home: bool


_MODEL_DEFINITIONS = (
    MachineModelDefinition(
        key="idraw-a4",
        label="iDraw A4",
        runtime_model=1,
        width_mm=300,
        height_mm=210,
        physical_home="bottom-right",
        my_home_corner="top-left",
        long_axis_is_y=True,
        x_axis_toward_home=False,
        y_axis_toward_home=True,
    ),
    MachineModelDefinition(
        key="idraw-a3",
        label="iDraw A3",
        runtime_model=2,
        width_mm=430,
        height_mm=297,
        physical_home="bottom-right",
        my_home_corner="top-left",
        long_axis_is_y=True,
        x_axis_toward_home=False,
        y_axis_toward_home=True,
    ),
    MachineModelDefinition(
        key="idraw-a2",
        label="iDraw A2",
        runtime_model=6,
        width_mm=594,
        height_mm=432,
        physical_home="bottom-right",
        my_home_corner="top-left",
        long_axis_is_y=True,
        x_axis_toward_home=False,
        y_axis_toward_home=True,
    ),
    MachineModelDefinition(
        key="idraw-a1",
        label="iDraw A1",
        runtime_model=5,
        width_mm=864,
        height_mm=594,
        physical_home="bottom-right",
        my_home_corner="top-left",
        long_axis_is_y=True,
        x_axis_toward_home=False,
        y_axis_toward_home=True,
    ),
    MachineModelDefinition(
        key="idraw-a0",
        label="iDraw A0",
        runtime_model=8,
        width_mm=1189,
        height_mm=841,
        physical_home="bottom-right",
        my_home_corner="top-left",
        long_axis_is_y=True,
        x_axis_toward_home=False,
        y_axis_toward_home=True,
    ),
    # MachineModelDefinition(
    #     key="idraw-lab-reverse",
    #     label="iDraw Lab Reverse",
    #     runtime_model=6,
    #     width_mm=500,
    #     height_mm=350,
    #     physical_home="bottom-left",
    #     my_home_corner="top-right",
    #     long_axis_is_y=False,
    #     x_axis_toward_home=True,
    #     y_axis_toward_home=False,
    # ),
)

MACHINE_MODELS = {model.key: model for model in _MODEL_DEFINITIONS}

_MODEL_ALIASES = {
    "idraw-1.0": "idraw-a1",
    "idraw-2.0": "idraw-a2",
    "idraw a0": "idraw-a0",
    "idraw a1": "idraw-a1",
    "idraw a2": "idraw-a2",
    "idraw a3": "idraw-a3",
    "idraw a4": "idraw-a4",
}


def list_machine_models() -> list[MachineModelDefinition]:
    return list(_MODEL_DEFINITIONS)


def _is_portrait(display_orientation: str) -> bool:
    return display_orientation.strip().lower() == "portrait"


def rotate_corner(corner: str, *, clockwise: bool) -> str:
    index = MACHINE_HOME_CORNERS.index(corner)
    if clockwise:
        return MACHINE_HOME_CORNERS[(index + 1) % len(MACHINE_HOME_CORNERS)]
    return MACHINE_HOME_CORNERS[(index - 1) % len(MACHINE_HOME_CORNERS)]


def display_home_corner(model: MachineModelDefinition, display_orientation: str) -> str:
    if _is_portrait(display_orientation):
        return model.physical_home
    return rotate_corner(model.physical_home, clockwise=True)


def display_axis_vectors(
    model: MachineModelDefinition,
    display_orientation: str,
) -> tuple[tuple[int, int], tuple[int, int]]:
    home_corner = display_home_corner(model, display_orientation)
    long_side_is_horizontal = not _is_portrait(display_orientation)

    if long_side_is_horizontal:
        long_side_toward_home = (-1, 0) if "left" in home_corner else (1, 0)
        short_side_toward_home = (0, -1) if "top" in home_corner else (0, 1)
    else:
        long_side_toward_home = (0, -1) if "top" in home_corner else (0, 1)
        short_side_toward_home = (-1, 0) if "left" in home_corner else (1, 0)

    if model.long_axis_is_y:
        x_toward_home = short_side_toward_home
        y_toward_home = long_side_toward_home
    else:
        x_toward_home = long_side_toward_home
        y_toward_home = short_side_toward_home

    x_axis = (
        x_toward_home
        if model.x_axis_toward_home
        else (-x_toward_home[0], -x_toward_home[1])
    )
    y_axis = (
        y_toward_home
        if model.y_axis_toward_home
        else (-y_toward_home[0], -y_toward_home[1])
    )
    return x_axis, y_axis


def corner_delta_from_home(
    home_corner: str,
    target_corner: str,
    *,
    width_mm: float,
    height_mm: float,
    padding_mm: float = 0.0,
) -> tuple[float, float]:
    home_x = -1.0 if "left" in home_corner else 1.0
    home_y = -1.0 if "top" in home_corner else 1.0
    target_x = -1.0 if "left" in target_corner else 1.0
    target_y = -1.0 if "top" in target_corner else 1.0

    delta_x = (
        0.0 if target_x == home_x else (width_mm if target_x > home_x else -width_mm)
    )
    delta_y = (
        0.0 if target_y == home_y else (height_mm if target_y > home_y else -height_mm)
    )
    if padding_mm > 0.0:
        delta_x += padding_mm if "left" in target_corner else -padding_mm
        delta_y += padding_mm if "top" in target_corner else -padding_mm
    return delta_x, delta_y


def move_delta_to_corner(
    model: MachineModelDefinition,
    display_orientation: str,
    target_corner: str,
    *,
    padding_mm: float = 0.0,
) -> tuple[float, float]:
    orientation = display_orientation.strip().lower()
    display_width_mm = model.height_mm if orientation == "portrait" else model.width_mm
    display_height_mm = model.width_mm if orientation == "portrait" else model.height_mm
    home_corner = display_home_corner(model, orientation)
    delta_x, delta_y = corner_delta_from_home(
        home_corner,
        target_corner,
        width_mm=display_width_mm,
        height_mm=display_height_mm,
        padding_mm=padding_mm,
    )
    x_axis, y_axis = display_axis_vectors(model, orientation)
    x_mm = (delta_x * x_axis[0]) + (delta_y * x_axis[1])
    y_mm = (delta_x * y_axis[0]) + (delta_y * y_axis[1])
    return x_mm, y_mm


def move_delta_to_center(
    model: MachineModelDefinition,
    display_orientation: str,
) -> tuple[float, float]:
    orientation = display_orientation.strip().lower()
    display_width_mm = model.height_mm if orientation == "portrait" else model.width_mm
    display_height_mm = model.width_mm if orientation == "portrait" else model.height_mm
    home_corner = display_home_corner(model, orientation)

    delta_x = (
        display_width_mm / 2.0 if "left" in home_corner else -(display_width_mm / 2.0)
    )
    delta_y = (
        display_height_mm / 2.0 if "top" in home_corner else -(display_height_mm / 2.0)
    )

    x_axis, y_axis = display_axis_vectors(model, orientation)
    x_mm = (delta_x * x_axis[0]) + (delta_y * x_axis[1])
    y_mm = (delta_x * y_axis[0]) + (delta_y * y_axis[1])
    return x_mm, y_mm


def table_relative_jog_vector(
    model: MachineModelDefinition,
    display_orientation: str,
    direction: str,
) -> tuple[float, float]:
    orientation = display_orientation.strip().lower()
    x_axis, y_axis = display_axis_vectors(model, orientation)
    normalized = direction.strip().lower()
    table_directions = {
        "right": (1, 0),
        "left": (-1, 0),
        "forward": (0, -1),
        "backward": (0, 1),
    }
    desired_dx, desired_dy = table_directions[normalized]

    x_mm = float((desired_dx * x_axis[0]) + (desired_dy * x_axis[1]))
    y_mm = float((desired_dx * y_axis[0]) + (desired_dy * y_axis[1]))
    return x_mm, y_mm


def logical_home_mirror_axes(home_corner: str) -> tuple[bool, bool]:
    normalized = home_corner.strip().lower()
    if normalized not in MACHINE_HOME_CORNERS:
        raise ValueError(f"Unknown logical home corner: {home_corner}")

    mirror_x = "top" in normalized
    mirror_y = "right" in normalized
    return mirror_x, mirror_y


def get_machine_model(model_name: str) -> MachineModelDefinition:
    normalized = model_name.strip().lower()
    normalized = _MODEL_ALIASES.get(normalized, normalized)
    return MACHINE_MODELS.get(normalized, MACHINE_MODELS["idraw-a2"])
