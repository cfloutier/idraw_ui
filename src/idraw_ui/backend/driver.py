from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from idraw_ui.backend.models import MachineProfile, PlotProgress, PlotState
from idraw_ui.backend.vendor_bridge import VendorBridge, VendorBridgeError


@dataclass
class DriverCommandResult:
    ok: bool
    message: str = ""


class Driver:
    """Application-facing driver abstraction."""

    def __init__(
        self,
        profile: Optional[MachineProfile] = None,
        bridge: VendorBridge | None = None,
    ) -> None:
        self.profile = profile or MachineProfile()
        self.progress = PlotProgress()
        self.bridge = bridge or VendorBridge()

    def connect(self) -> DriverCommandResult:
        try:
            self.bridge.connect()
            self.progress.state = PlotState.READY
            self.progress.message = "Connected"
            return DriverCommandResult(ok=True, message="connected")
        except VendorBridgeError as exc:
            self.progress.state = PlotState.IDLE
            self.progress.message = f"Connect failed: {exc}"
            return DriverCommandResult(ok=False, message=str(exc))

    def disconnect(self) -> DriverCommandResult:
        self.bridge.disconnect()
        self.progress.state = PlotState.IDLE
        self.progress.message = "Disconnected"
        return DriverCommandResult(ok=True, message="disconnected")

    def status(self) -> DriverCommandResult:
        try:
            status = self.bridge.get_status()
            self.progress.message = f"Status: {status}"
            return DriverCommandResult(ok=True, message=status)
        except VendorBridgeError as exc:
            return DriverCommandResult(ok=False, message=str(exc))

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
        try:
            response = self.bridge.home()
            self.progress.state = PlotState.READY
            self.progress.message = "Homing completed"
            return DriverCommandResult(ok=True, message=response)
        except VendorBridgeError as exc:
            self.progress.state = PlotState.IDLE
            self.progress.message = f"Homing failed: {exc}"
            return DriverCommandResult(ok=False, message=str(exc))

    def raise_pen(self) -> DriverCommandResult:
        try:
            response = self.bridge.raise_pen()
            self.progress.message = "Pen raised"
            return DriverCommandResult(ok=True, message=response)
        except VendorBridgeError as exc:
            return DriverCommandResult(ok=False, message=str(exc))

    def lower_pen(self) -> DriverCommandResult:
        try:
            response = self.bridge.lower_pen()
            self.progress.message = "Pen lowered"
            return DriverCommandResult(ok=True, message=response)
        except VendorBridgeError as exc:
            return DriverCommandResult(ok=False, message=str(exc))

    def get_progress(self) -> PlotProgress:
        return self.progress
