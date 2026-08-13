from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PlotState(str, Enum):
    IDLE = "idle"
    READY = "ready"
    DRAWING = "drawing"
    PAUSING = "pausing"
    PAUSED = "paused"
    HOMING = "homing"
    STOPPING = "stopping"


@dataclass
class MachineSettings:
    name: str = "machine-default"
    machine_model: str = "idraw-2.0"
    table_orientation: str = "landscape"
    my_home_corner: str = "top-left"
    drawing_margin_top_mm: int = 10
    drawing_margin_bottom_mm: int = 10
    drawing_margin_left_mm: int = 10
    drawing_margin_right_mm: int = 10
    port: str | None = None
    baudrate: int = 115200
    serial_timeout: float = 1.0
    digest: int = 1


@dataclass
class PlotProfile:
    name: str = "default"
    pen_up_height: float = 0.5
    pen_down_height: float = 5.0
    pen_move_speed: float | None = None
    speed_penup: float = 8000.0
    speed_pendown: float = 2000.0
    accel: float = 75.0
    reordering: int = 0
    digest: int = 1
    pen_up_command: str | None = None
    pen_down_command: str | None = None


@dataclass
class AppState:
    active_profile: str = "default"
    active_tab: str = "Jog"
    jog_distance_mm: float = 10.0
    jog_mode: str = "physical"
    last_svg_file: str | None = None
    last_folder: str | None = None


@dataclass
class PlotProgress:
    state: PlotState = PlotState.IDLE
    elapsed_seconds: float = 0.0
    estimated_seconds: float | None = None
    last_run_duration_seconds: float | None = None
    distance_pen_down_mm: float = 0.0
    distance_total_mm: float = 0.0
    pen_lifts: int = 0
    message: str = ""
