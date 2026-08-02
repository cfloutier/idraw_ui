from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from idraw_ui.backend.models import (
    MachineSettings,
    PlotProfile,
    PlotProgress,
    PlotState,
)
from idraw_ui.backend.profiles import load_machine_settings, load_plot_profile
from idraw_ui.backend.vendor_bridge import VendorBridge, VendorBridgeError


@dataclass
class DriverCommandResult:
    ok: bool
    message: str = ""


class Driver:
    """Application-facing driver abstraction."""

    def __init__(
        self,
        machine_settings: Optional[MachineSettings] = None,
        plot_profile: Optional[PlotProfile] = None,
        bridge: VendorBridge | None = None,
    ) -> None:
        self.machine_settings = machine_settings or MachineSettings()
        self.plot_profile = plot_profile or PlotProfile()
        self.progress = PlotProgress()
        if bridge is not None:
            self.bridge = bridge
        else:
            self.bridge = VendorBridge(
                port=self.machine_settings.port,
                baudrate=self.machine_settings.baudrate,
                timeout=self.machine_settings.serial_timeout,
                pen_up_command=self.plot_profile.pen_up_command,
                pen_down_command=self.plot_profile.pen_down_command,
                pen_up_z=self.plot_profile.pen_up_height,
                pen_down_z=self.plot_profile.pen_down_height,
                pen_move_speed=self.plot_profile.pen_move_speed
                or self.plot_profile.speed_penup,
                speed_penup=self.plot_profile.speed_penup,
                speed_pendown=self.plot_profile.speed_pendown,
            )

    @classmethod
    def from_config_files(
        cls,
        machine_settings_path: str | Path,
        plot_profile_path: str | Path,
    ) -> "Driver":
        return cls(
            machine_settings=load_machine_settings(machine_settings_path),
            plot_profile=load_plot_profile(plot_profile_path),
        )

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
        except Exception as exc:
            self.progress.state = PlotState.IDLE
            self.progress.message = f"Connect failed: {exc}"
            return DriverCommandResult(ok=False, message=str(exc))

    def disconnect(self) -> DriverCommandResult:
        try:
            self.bridge.disconnect()
            self.progress.state = PlotState.IDLE
            self.progress.message = "Disconnected"
            return DriverCommandResult(ok=True, message="disconnected")
        except VendorBridgeError as exc:
            self.progress.state = PlotState.IDLE
            self.progress.message = f"Disconnect failed: {exc}"
            return DriverCommandResult(ok=False, message=str(exc))
        except Exception as exc:
            self.progress.state = PlotState.IDLE
            self.progress.message = f"Disconnect failed: {exc}"
            return DriverCommandResult(ok=False, message=str(exc))

    def status(self) -> DriverCommandResult:
        try:
            status = self.bridge.get_status()
            self.progress.state = PlotState.READY
            self.progress.message = f"Status: {status}"
            return DriverCommandResult(ok=True, message=status)
        except VendorBridgeError as exc:
            self.progress.message = f"Status failed: {exc}"
            return DriverCommandResult(ok=False, message=str(exc))
        except Exception as exc:
            self.progress.message = f"Status failed: {exc}"
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
        except Exception as exc:
            self.progress.state = PlotState.IDLE
            self.progress.message = f"Homing failed: {exc}"
            return DriverCommandResult(ok=False, message=str(exc))

    def raise_pen(self) -> DriverCommandResult:
        try:
            response = self.bridge.raise_pen()
            self.progress.state = PlotState.READY
            self.progress.message = "Pen raised"
            return DriverCommandResult(ok=True, message=response)
        except VendorBridgeError as exc:
            self.progress.message = f"Pen raise failed: {exc}"
            return DriverCommandResult(ok=False, message=str(exc))
        except Exception as exc:
            self.progress.message = f"Pen raise failed: {exc}"
            return DriverCommandResult(ok=False, message=str(exc))

    def lower_pen(self) -> DriverCommandResult:
        try:
            response = self.bridge.lower_pen()
            self.progress.state = PlotState.READY
            self.progress.message = "Pen lowered"
            return DriverCommandResult(ok=True, message=response)
        except VendorBridgeError as exc:
            self.progress.message = f"Pen lower failed: {exc}"
            return DriverCommandResult(ok=False, message=str(exc))
        except Exception as exc:
            self.progress.message = f"Pen lower failed: {exc}"
            return DriverCommandResult(ok=False, message=str(exc))

    def get_progress(self) -> PlotProgress:
        return self.progress
