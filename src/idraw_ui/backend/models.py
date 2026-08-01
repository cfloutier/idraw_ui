from __future__ import annotations

from dataclasses import dataclass, field
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
class MachineProfile:
    name: str = "default"
    machine_model: str = "default"
    pen_up_height: float = 0.5
    pen_down_height: float = 5.0
    speed_penup: float = 8000.0
    speed_pendown: float = 2000.0
    accel: float = 75.0
    auto_rotate: bool = True
    reordering: int = 0
    preview: bool = False
    digest: int = 1
    field: dict[str, object] = field(default_factory=dict)


@dataclass
class PlotProgress:
    state: PlotState = PlotState.IDLE
    elapsed_seconds: float = 0.0
    estimated_seconds: Optional[float] = None
    distance_pen_down_mm: float = 0.0
    distance_total_mm: float = 0.0
    pen_lifts: int = 0
    message: str = ""
