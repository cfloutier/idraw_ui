from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from idraw_ui.backend.models import MachineProfile, PlotProgress, PlotState


@dataclass
class DriverCommandResult:
    ok: bool
    message: str = ""


class Driver:
    """Application-facing driver abstraction."""

    def __init__(self, profile: Optional[MachineProfile] = None) -> None:
        self.profile = profile or MachineProfile()
        self.progress = PlotProgress()

    def load_svg(self, path: str) -> DriverCommandResult:
        return DriverCommandResult(ok=True, message=f"Loaded SVG: {path}")

    def estimate(self) -> DriverCommandResult:
        self.progress.state = PlotState.READY
        self.progress.message = "Estimation placeholder"
        return DriverCommandResult(ok=True, message="estimation placeholder")

    def start(self) -> DriverCommandResult:
        self.progress.state = PlotState.DRAWING
        self.progress.message = "Start placeholder"
        return DriverCommandResult(ok=True, message="start placeholder")

    def pause(self) -> DriverCommandResult:
        self.progress.state = PlotState.PAUSED
        self.progress.message = "Pause placeholder"
        return DriverCommandResult(ok=True, message="pause placeholder")

    def resume(self) -> DriverCommandResult:
        self.progress.state = PlotState.DRAWING
        self.progress.message = "Resume placeholder"
        return DriverCommandResult(ok=True, message="resume placeholder")

    def home(self) -> DriverCommandResult:
        self.progress.state = PlotState.HOMING
        self.progress.message = "Home placeholder"
        return DriverCommandResult(ok=True, message="home placeholder")

    def raise_pen(self) -> DriverCommandResult:
        return DriverCommandResult(ok=True, message="raise pen placeholder")

    def lower_pen(self) -> DriverCommandResult:
        return DriverCommandResult(ok=True, message="lower pen placeholder")

    def get_progress(self) -> PlotProgress:
        return self.progress
