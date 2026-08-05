from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


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
    port: str | None = None
    baudrate: int = 115200
    serial_timeout: float = 1.0


@dataclass
class PlotProfile:
    name: str = "default"
    pen_up_height: float = 0.5
    pen_down_height: float = 5.0
    pen_move_speed: float | None = None
    speed_penup: float = 8000.0
    speed_pendown: float = 2000.0
    accel: float = 75.0
    auto_rotate: bool = True
    reordering: int = 0
    preview: bool = False
    digest: int = 1
    pen_up_command: str | None = None
    pen_down_command: str | None = None


@dataclass
class AppState:
    active_profile: str = "default"
    active_tab: str = "Jog"
    jog_distance_mm: float = 10.0
    last_svg_file: str | None = None
    last_folder: str | None = None


@dataclass
class PlotProgress:
    state: PlotState = PlotState.IDLE
    elapsed_seconds: float = 0.0
    estimated_seconds: Optional[float] = None
    distance_pen_down_mm: float = 0.0
    distance_total_mm: float = 0.0
    pen_lifts: int = 0
    message: str = ""
