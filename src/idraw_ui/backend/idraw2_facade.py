from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from idraw_ui.backend.idraw2_runtime import Idraw2InternalRuntime
from idraw_ui.backend.models import (
    MachineSettings,
    PlotProfile,
    PlotProgress,
    PlotState,
)


@dataclass
class EngineCommandResult:
    ok: bool
    message: str = ""


@runtime_checkable
class IdrawRuntime(Protocol):
    def configure(
        self,
        machine_settings: MachineSettings,
        plot_profile: PlotProfile,
    ) -> None: ...

    def load_svg(self, path: Path) -> None: ...

    def prepare(self) -> dict[str, Any] | None: ...

    def start(self) -> None: ...

    def pause(self) -> None: ...

    def resume(self) -> None: ...

    def stop(self) -> None: ...

    def home(self) -> None: ...

    def get_status(self) -> dict[str, Any]: ...


def _default_runtime_factory() -> IdrawRuntime:
    return Idraw2InternalRuntime()


class Idraw2Facade:
    """UI-facing facade for future idraw2_0internal runtime integration."""

    def __init__(
        self,
        machine_settings: MachineSettings | None = None,
        plot_profile: PlotProfile | None = None,
        runtime: IdrawRuntime | None = None,
    ) -> None:
        self.machine_settings = machine_settings or MachineSettings()
        self.plot_profile = plot_profile or PlotProfile()
        self.runtime = runtime or _default_runtime_factory()
        self.progress = PlotProgress()
        self.svg_path: Path | None = None
        self._is_prepared = False

        try:
            self.runtime.configure(self.machine_settings, self.plot_profile)
        except Exception as exc:
            self.progress.state = PlotState.IDLE
            self.progress.message = f"Runtime configure failed: {exc}"

    def _fail(
        self, message: str, *, state: PlotState | None = None
    ) -> EngineCommandResult:
        if state is not None:
            self.progress.state = state
        self.progress.message = message
        return EngineCommandResult(ok=False, message=message)

    def _require_runtime(self) -> EngineCommandResult | None:
        if self.runtime is None:
            return self._fail("Runtime backend is not configured", state=PlotState.IDLE)
        return None

    def _refresh_from_runtime_status(self) -> None:
        runtime_error = self._require_runtime()
        if runtime_error is not None:
            return

        try:
            status = self.runtime.get_status()
        except Exception:
            return

        state = status.get("state")
        if isinstance(state, PlotState):
            self.progress.state = state
        elif isinstance(state, str):
            try:
                self.progress.state = PlotState(state)
            except ValueError:
                pass

        estimated_seconds = status.get("estimated_seconds")
        if estimated_seconds is not None:
            self.progress.estimated_seconds = float(estimated_seconds)

        elapsed_seconds = status.get("elapsed_seconds")
        if elapsed_seconds is not None:
            self.progress.elapsed_seconds = float(elapsed_seconds)

        distance_pen_down_mm = status.get("distance_pen_down_mm")
        if distance_pen_down_mm is not None:
            self.progress.distance_pen_down_mm = float(distance_pen_down_mm)

        distance_total_mm = status.get("distance_total_mm")
        if distance_total_mm is not None:
            self.progress.distance_total_mm = float(distance_total_mm)

        pen_lifts = status.get("pen_lifts")
        if pen_lifts is not None:
            self.progress.pen_lifts = int(pen_lifts)

        message = status.get("message")
        if message:
            self.progress.message = str(message)

    def load_svg(self, path: str | Path) -> EngineCommandResult:
        runtime_error = self._require_runtime()
        if runtime_error is not None:
            return runtime_error

        svg_path = Path(path)
        if not svg_path.exists():
            return self._fail(f"SVG file not found: {svg_path}", state=PlotState.IDLE)

        try:
            self.runtime.load_svg(svg_path)
        except Exception as exc:
            return self._fail(f"Load failed: {exc}", state=PlotState.IDLE)

        self.svg_path = svg_path
        self._is_prepared = False
        self.progress.state = PlotState.READY
        self.progress.message = f"Loaded SVG: {svg_path}"
        return EngineCommandResult(ok=True, message="loaded")

    def prepare(self) -> EngineCommandResult:
        runtime_error = self._require_runtime()
        if runtime_error is not None:
            return runtime_error
        if self.svg_path is None:
            return self._fail("No SVG loaded", state=PlotState.IDLE)

        try:
            metrics = self.runtime.prepare() or {}
        except Exception as exc:
            self._is_prepared = False
            return self._fail(f"Prepare failed: {exc}", state=PlotState.IDLE)

        if "estimated_seconds" in metrics:
            self.progress.estimated_seconds = float(metrics["estimated_seconds"])
        if "distance_pen_down_mm" in metrics:
            self.progress.distance_pen_down_mm = float(metrics["distance_pen_down_mm"])
        if "distance_total_mm" in metrics:
            self.progress.distance_total_mm = float(metrics["distance_total_mm"])
        if "pen_lifts" in metrics:
            self.progress.pen_lifts = int(metrics["pen_lifts"])

        self._is_prepared = True
        self.progress.state = PlotState.READY
        self.progress.message = "Prepared"
        return EngineCommandResult(ok=True, message="prepared")

    def start(self) -> EngineCommandResult:
        runtime_error = self._require_runtime()
        if runtime_error is not None:
            return runtime_error
        if self.svg_path is None:
            return self._fail("No SVG loaded", state=PlotState.IDLE)
        if not self._is_prepared:
            result = self.prepare()
            if not result.ok:
                return result

        try:
            self.runtime.start()
        except Exception as exc:
            return self._fail(f"Start failed: {exc}", state=PlotState.IDLE)

        self.progress.state = PlotState.DRAWING
        self.progress.message = "Drawing"
        return EngineCommandResult(ok=True, message="drawing")

    def pause(self) -> EngineCommandResult:
        runtime_error = self._require_runtime()
        if runtime_error is not None:
            return runtime_error
        if self.progress.state != PlotState.DRAWING:
            return self._fail("Cannot pause when not drawing")

        self.progress.state = PlotState.PAUSING
        try:
            self.runtime.pause()
        except Exception as exc:
            return self._fail(f"Pause failed: {exc}", state=PlotState.DRAWING)

        self.progress.state = PlotState.PAUSED
        self.progress.message = "Paused"
        return EngineCommandResult(ok=True, message="paused")

    def resume(self) -> EngineCommandResult:
        runtime_error = self._require_runtime()
        if runtime_error is not None:
            return runtime_error
        if self.progress.state != PlotState.PAUSED:
            return self._fail("Cannot resume when not paused")

        try:
            self.runtime.resume()
        except Exception as exc:
            return self._fail(f"Resume failed: {exc}", state=PlotState.PAUSED)

        self.progress.state = PlotState.DRAWING
        self.progress.message = "Resumed"
        return EngineCommandResult(ok=True, message="resumed")

    def stop(self) -> EngineCommandResult:
        runtime_error = self._require_runtime()
        if runtime_error is not None:
            return runtime_error

        self.progress.state = PlotState.STOPPING
        try:
            self.runtime.stop()
        except Exception as exc:
            return self._fail(f"Stop failed: {exc}", state=PlotState.IDLE)

        self.progress.state = PlotState.READY
        self.progress.message = "Stopped"
        return EngineCommandResult(ok=True, message="stopped")

    def home(self) -> EngineCommandResult:
        runtime_error = self._require_runtime()
        if runtime_error is not None:
            return runtime_error

        self.progress.state = PlotState.HOMING
        try:
            self.runtime.home()
        except Exception as exc:
            return self._fail(f"Home failed: {exc}", state=PlotState.IDLE)

        self.progress.state = PlotState.READY
        self.progress.message = "Homing completed"
        return EngineCommandResult(ok=True, message="homed")

    def get_progress(self) -> PlotProgress:
        self._refresh_from_runtime_status()
        return self.progress
