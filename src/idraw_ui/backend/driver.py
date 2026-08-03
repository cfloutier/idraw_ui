from __future__ import annotations

from dataclasses import replace
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from idraw_ui.backend.idraw2_facade import Idraw2Facade
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
        plot_facade: Idraw2Facade | None = None,
    ) -> None:
        self.machine_settings = machine_settings or MachineSettings()
        self.plot_profile = plot_profile or PlotProfile()
        self.progress = PlotProgress()
        self.plot_facade = plot_facade or Idraw2Facade(
            machine_settings=self.machine_settings,
            plot_profile=self.plot_profile,
        )
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
        release_error = self._release_bridge_for_plot_runtime()
        if release_error is not None:
            return release_error
        result = self.plot_facade.load_svg(path)
        self._sync_progress(self.plot_facade.get_progress())
        return DriverCommandResult(ok=result.ok, message=result.message)

    def estimate(self) -> DriverCommandResult:
        release_error = self._release_bridge_for_plot_runtime()
        if release_error is not None:
            return release_error
        result = self.plot_facade.prepare()
        self._sync_progress(self.plot_facade.get_progress())
        return DriverCommandResult(ok=result.ok, message=result.message)

    def start(self) -> DriverCommandResult:
        release_error = self._release_bridge_for_plot_runtime()
        if release_error is not None:
            return release_error
        result = self.plot_facade.start()
        self._sync_progress(self.plot_facade.get_progress())
        return DriverCommandResult(ok=result.ok, message=result.message)

    def pause(self) -> DriverCommandResult:
        release_error = self._release_bridge_for_plot_runtime()
        if release_error is not None:
            return release_error
        result = self.plot_facade.pause()
        self._sync_progress(self.plot_facade.get_progress())
        return DriverCommandResult(ok=result.ok, message=result.message)

    def resume(self) -> DriverCommandResult:
        release_error = self._release_bridge_for_plot_runtime()
        if release_error is not None:
            return release_error
        result = self.plot_facade.resume()
        self._sync_progress(self.plot_facade.get_progress())
        return DriverCommandResult(ok=result.ok, message=result.message)

    def stop(self) -> DriverCommandResult:
        release_error = self._release_bridge_for_plot_runtime()
        if release_error is not None:
            return release_error
        result = self.plot_facade.stop()
        self._sync_progress(self.plot_facade.get_progress())
        return DriverCommandResult(ok=result.ok, message=result.message)

    def update_plot_profile(self, **changes: object) -> None:
        self.plot_profile = replace(self.plot_profile, **changes)
        self.bridge.pen_up_command = self.plot_profile.pen_up_command
        self.bridge.pen_down_command = self.plot_profile.pen_down_command
        self.bridge.pen_up_z = self.plot_profile.pen_up_height
        self.bridge.pen_down_z = self.plot_profile.pen_down_height
        self.bridge.pen_move_speed = (
            self.plot_profile.pen_move_speed or self.plot_profile.speed_penup
        )
        self.bridge.speed_penup = self.plot_profile.speed_penup
        self.bridge.speed_pendown = self.plot_profile.speed_pendown
        self.plot_facade.reconfigure(
            machine_settings=self.machine_settings,
            plot_profile=self.plot_profile,
        )

    def update_machine_settings(self, **changes: object) -> None:
        self.machine_settings = replace(self.machine_settings, **changes)
        self.bridge.port = self.machine_settings.port
        self.bridge.baudrate = self.machine_settings.baudrate
        self.bridge.timeout = self.machine_settings.serial_timeout
        self.plot_facade.reconfigure(
            machine_settings=self.machine_settings,
            plot_profile=self.plot_profile,
        )

    def home(self) -> DriverCommandResult:
        return self._run_bridge_action_with_auto_disconnect(
            self.bridge.home,
            working_state=PlotState.HOMING,
            success_message="Homing completed",
            failure_prefix="Homing failed",
        )

    def center_for_test(self) -> DriverCommandResult:
        def do_center() -> str:
            self.bridge.home()
            self.bridge.raise_pen()
            return self.bridge.move_relative(
                x_mm=300.0,
                y_mm=-400.0,
                feed_mm_min=self.plot_profile.speed_penup,
            )

        return self._run_bridge_action_with_auto_disconnect(
            do_center,
            working_state=PlotState.HOMING,
            success_message="Center move completed (home + +300/-400 mm)",
            failure_prefix="Center move failed",
        )

    def jog_for_test(self, x_mm: float, y_mm: float) -> DriverCommandResult:
        def do_jog() -> str:
            self.bridge.raise_pen()
            return self.bridge.move_relative(
                x_mm=x_mm,
                y_mm=y_mm,
                feed_mm_min=self.plot_profile.speed_penup,
            )

        return self._run_bridge_action_with_auto_disconnect(
            do_jog,
            working_state=None,
            success_message=f"Jog move completed ({x_mm:+.1f}, {y_mm:+.1f} mm)",
            failure_prefix="Jog move failed",
        )

    def raise_pen(self) -> DriverCommandResult:
        return self._run_bridge_action_with_auto_disconnect(
            self.bridge.raise_pen,
            working_state=None,
            success_message="Pen raised",
            failure_prefix="Pen raise failed",
        )

    def lower_pen(self) -> DriverCommandResult:
        return self._run_bridge_action_with_auto_disconnect(
            self.bridge.lower_pen,
            working_state=None,
            success_message="Pen lowered",
            failure_prefix="Pen lower failed",
        )

    def _sync_progress(self, source: PlotProgress) -> None:
        self.progress.state = source.state
        self.progress.elapsed_seconds = source.elapsed_seconds
        self.progress.estimated_seconds = source.estimated_seconds
        self.progress.distance_pen_down_mm = source.distance_pen_down_mm
        self.progress.distance_total_mm = source.distance_total_mm
        self.progress.pen_lifts = source.pen_lifts
        self.progress.message = source.message

    def get_progress(self) -> PlotProgress:
        plot_progress = self.plot_facade.get_progress()
        if self.plot_facade.svg_path is not None or plot_progress.state in {
            PlotState.DRAWING,
            PlotState.PAUSING,
            PlotState.PAUSED,
            PlotState.STOPPING,
        }:
            self._sync_progress(plot_progress)
        return self.progress

    def _release_bridge_for_plot_runtime(self) -> DriverCommandResult | None:
        if not self.bridge.connected:
            return None

        try:
            self.bridge.disconnect()
        except VendorBridgeError as exc:
            self.progress.message = f"Bridge release failed before plot runtime: {exc}"
            return DriverCommandResult(ok=False, message=str(exc))
        except Exception as exc:
            self.progress.message = f"Bridge release failed before plot runtime: {exc}"
            return DriverCommandResult(ok=False, message=str(exc))

        return None

    def _run_bridge_action_with_auto_disconnect(
        self,
        action: Callable[[], str],
        *,
        working_state: PlotState | None,
        success_message: str,
        failure_prefix: str,
    ) -> DriverCommandResult:
        if working_state is not None:
            self.progress.state = working_state

        action_error: Exception | None = None
        response = ""
        try:
            self.bridge.connect()
            response = action()
        except VendorBridgeError as exc:
            action_error = exc
        except Exception as exc:
            action_error = exc

        disconnect_error: Exception | None = None
        try:
            self.bridge.disconnect()
        except Exception as exc:
            disconnect_error = exc

        if action_error is not None:
            self.progress.state = PlotState.IDLE
            if disconnect_error is not None:
                self.progress.message = f"{failure_prefix}: {action_error} | auto-disconnect failed: {disconnect_error}"
                return DriverCommandResult(
                    ok=False,
                    message=f"{action_error} | auto-disconnect failed: {disconnect_error}",
                )

            self.progress.message = f"{failure_prefix}: {action_error}"
            return DriverCommandResult(ok=False, message=str(action_error))

        if disconnect_error is not None:
            self.progress.state = PlotState.IDLE
            self.progress.message = (
                f"{success_message}, but auto-disconnect failed: {disconnect_error}"
            )
            return DriverCommandResult(ok=False, message=str(disconnect_error))

        self.progress.state = PlotState.IDLE
        self.progress.message = f"{success_message} (auto-disconnected)"
        return DriverCommandResult(ok=True, message=response)
