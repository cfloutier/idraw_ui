from __future__ import annotations

import copy
import os
import tempfile
import threading
import time
from collections.abc import Callable
from optparse import Option, OptionParser
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from lxml import etree

from idraw_ui.backend.machine_models import (
    get_machine_model,
    logical_home_mirror_axes,
)
from idraw_ui.backend.models import MachineSettings, PlotProfile, PlotState

_LOGICAL_HOME_METADATA_KEY = "idraw_ui_logical_home"
_CONTENT_ORIENTATION_METADATA_KEY = "idraw_ui_content_orientation"
_UPRIGHT_CONTENT_VERSION = "upright-v1"


def _mirror_digest(digest: Any, *, mirror_x: bool, mirror_y: bool) -> None:
    if not mirror_x and not mirror_y:
        return
    for layer in digest.layers:
        for path in layer.paths:
            for subpath in path.subpaths:
                for vertex in subpath:
                    if mirror_x:
                        vertex[0] = digest.width - vertex[0]
                    if mirror_y:
                        vertex[1] = digest.height - vertex[1]


def _apply_logical_home_to_digest(
    session: Any, home_corner: str, *, orientation: str = "portrait"
) -> None:
    digest = session.digest
    is_landscape = orientation.strip().lower() == "landscape"
    if digest.metadata.get(_CONTENT_ORIENTATION_METADATA_KEY) != (
        _UPRIGHT_CONTENT_VERSION
    ):
        # portrait digest arrives 180° rotated; landscape arrives already upright
        if not is_landscape:
            _mirror_digest(digest, mirror_x=True, mirror_y=True)
        digest.metadata[_CONTENT_ORIENTATION_METADATA_KEY] = _UPRIGHT_CONTENT_VERSION

    target_mirror_x, target_mirror_y = logical_home_mirror_axes(home_corner)
    # landscape axes are 90° rotated: swap and invert mirror formula
    if is_landscape:
        target_mirror_x, target_mirror_y = target_mirror_y, not target_mirror_x

    digest.metadata[_LOGICAL_HOME_METADATA_KEY] = home_corner
    start_x = digest.width if target_mirror_x else 0.0
    start_y = digest.height if target_mirror_y else 0.0
    session.params.start_pos_x = start_x
    session.params.start_pos_y = start_y
    session.pen.phys.xpos = start_x
    session.pen.phys.ypos = start_y

    if session.options.digest:
        session.backup_original = copy.deepcopy(digest.to_plob())


def _default_session_factory() -> Any:
    from idraw2_0internal.idraw import iDraw

    def _parse_inkbool(_option: Option, _opt: str, value: str) -> bool:
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    class LegacyInkOption(Option):
        TYPES = Option.TYPES + ("inkbool",)
        TYPE_CHECKER = Option.TYPE_CHECKER.copy()
        TYPE_CHECKER["inkbool"] = _parse_inkbool

    class CompatIDraw(iDraw):
        """Bridge legacy OptionParser-based init with modern ink_extensions."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            # idraw2_0internal still configures options through self.OptionParser,
            # while recent ink_extensions.Effect exposes argparse via self.arg_parser.
            self.OptionParser = OptionParser(option_class=LegacyInkOption)
            super().__init__(*args, **kwargs)

        def prepare_document(self) -> bool:
            if not super().prepare_document():
                return False
            _apply_logical_home_to_digest(
                self,
                self._idraw_ui_logical_home_corner,
                orientation=self._idraw_ui_table_orientation,
            )
            return True

    return CompatIDraw(default_logging=False)


class Idraw2InternalRuntime:
    """Concrete runtime adapter around idraw2_0internal.iDraw."""

    def __init__(
        self,
        session_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._session_factory = session_factory or _default_session_factory
        self.machine_settings = MachineSettings()
        self.plot_profile = PlotProfile()
        self.svg_path: Path | None = None
        self._resume_svg_path: Path | None = None
        self._active_thread: threading.Thread | None = None
        self._active_session: Any | None = None
        self._pause_event = threading.Event()
        self._last_error: Exception | None = None
        self._lock = threading.Lock()
        self._last_metrics: dict[str, Any] = {}
        self._message = "Idle"
        self._state = PlotState.IDLE
        self._started_at: float | None = None

    def configure(
        self,
        machine_settings: MachineSettings,
        plot_profile: PlotProfile,
    ) -> None:
        self.machine_settings = machine_settings
        self.plot_profile = plot_profile
        self._message = "Configured"

    def load_svg(self, path: Path) -> None:
        svg_path = Path(path)
        if not svg_path.exists():
            raise FileNotFoundError(svg_path)
        self.svg_path = svg_path
        self._resume_svg_path = svg_path
        self._state = PlotState.READY
        self._message = f"Loaded SVG: {svg_path}"

    def prepare(self) -> dict[str, Any] | None:
        if self.svg_path is None:
            raise RuntimeError("No SVG loaded")

        session = self._build_session(
            mode="plot", preview=True, source_svg=self.svg_path
        )
        session.effect()
        self._persist_resume_snapshot(session)
        self._last_metrics = self._extract_metrics(session)
        self._state = PlotState.READY
        self._message = "Prepared"
        return self._last_metrics

    def start(self) -> None:
        if self.svg_path is None:
            raise RuntimeError("No SVG loaded")
        if self._thread_running():
            raise RuntimeError("Plot is already running")
        self._pause_event.clear()
        self._last_error = None
        self._started_at = time.time()
        self._state = PlotState.DRAWING
        self._message = "Drawing"
        self._start_worker(mode="plot", source_svg=self.svg_path)

    def pause(self) -> None:
        if not self._thread_running():
            raise RuntimeError("No active plot to pause")
        self._state = PlotState.PAUSING
        self._message = "Pausing"
        self._pause_event.set()
        self._join_active_thread()
        self._raise_if_worker_failed()
        self._state = PlotState.PAUSED
        self._message = "Paused"

    def resume(self) -> None:
        if self._thread_running():
            raise RuntimeError("Cannot resume while plot is still running")
        if self._resume_svg_path is None:
            raise RuntimeError("No paused plot data available to resume")
        self._pause_event.clear()
        self._last_error = None
        self._started_at = time.time()
        self._state = PlotState.DRAWING
        self._message = "Resumed"
        self._start_worker(
            mode="resume", source_svg=self._resume_svg_path, resume_type="plot"
        )

    def stop(self) -> None:
        if self._thread_running():
            self._state = PlotState.STOPPING
            self._message = "Stopping"
            self._pause_event.set()
            self._join_active_thread()
            self._raise_if_worker_failed()
        self._state = PlotState.READY
        self._message = "Stopped"

    def home(self) -> None:
        source = self._resume_svg_path or self.svg_path
        if source is None:
            raise RuntimeError("No SVG loaded")

        session = self._build_session(
            mode="resume",
            preview=False,
            source_svg=source,
            resume_type="home",
        )
        self._state = PlotState.HOMING
        self._message = "Homing"
        session.effect()
        self._persist_resume_snapshot(session)
        self._state = PlotState.READY
        self._message = "Homing completed"

    def get_status(self) -> dict[str, Any]:
        elapsed_seconds = 0.0
        if self._started_at is not None and self._thread_running():
            elapsed_seconds = max(0.0, time.time() - self._started_at)

        message = self._message
        if self._last_error is not None:
            message = str(self._last_error)

        status = {
            "state": self._state,
            "elapsed_seconds": elapsed_seconds,
            "message": message,
        }
        status.update(self._last_metrics)
        return status

    def _thread_running(self) -> bool:
        return self._active_thread is not None and self._active_thread.is_alive()

    def _join_active_thread(self, timeout_s: float = 30.0) -> None:
        if self._active_thread is None:
            return
        self._active_thread.join(timeout=timeout_s)
        if self._active_thread.is_alive():
            raise RuntimeError("Timed out waiting for plot worker")

    def _raise_if_worker_failed(self) -> None:
        if self._last_error is not None:
            raise self._last_error

    def _start_worker(
        self,
        *,
        mode: str,
        source_svg: Path,
        resume_type: str | None = None,
    ) -> None:
        def run_worker() -> None:
            try:
                session = self._build_session(
                    mode=mode,
                    preview=False,
                    source_svg=source_svg,
                    resume_type=resume_type,
                )
                with self._lock:
                    self._active_session = session
                session.effect()
                self._persist_resume_snapshot(session)
                self._last_metrics = self._extract_metrics(session)
                if self._pause_event.is_set():
                    self._state = PlotState.PAUSED
                    self._message = "Paused"
                else:
                    self._state = PlotState.READY
                    self._message = "Plot finished"
            except Exception as exc:  # noqa: BLE001  # pragma: no cover
                self._last_error = exc
                self._state = PlotState.IDLE
                self._message = str(exc)
            finally:
                with self._lock:
                    self._active_session = None
                self._started_at = None

        worker = threading.Thread(target=run_worker, daemon=True)
        self._active_thread = worker
        worker.start()

    def _build_session(
        self,
        *,
        mode: str,
        preview: bool,
        source_svg: Path,
        resume_type: str | None = None,
    ) -> Any:
        session = self._session_factory()
        if hasattr(session, "getoptions"):
            session.getoptions([])

        self._apply_options(
            session,
            mode=mode,
            preview=preview,
            resume_type=resume_type,
        )

        parser = etree.XMLParser(huge_tree=True)
        session.document = etree.parse(str(source_svg), parser=parser)
        session.original_document = session.document

        if hasattr(session, "set_up_pause_receiver"):
            session.set_up_pause_receiver(self._pause_event)

        return session

    def _apply_options(
        self,
        session: Any,
        *,
        mode: str,
        preview: bool,
        resume_type: str | None,
    ) -> None:
        options = getattr(session, "options", None)
        if options is None:
            options = SimpleNamespace()
            session.options = options

        option_parser = getattr(session, "OptionParser", None)
        if option_parser is not None and hasattr(option_parser, "defaults"):
            for key, value in option_parser.defaults.items():
                if key.startswith("_"):
                    continue
                if not hasattr(options, key):
                    setattr(options, key, value)

        params = getattr(session, "params", None)
        if params is not None:
            for key, value in vars(params).items():
                if key.startswith("_"):
                    continue
                if key in {"annotations"}:
                    continue
                if isinstance(value, (str, int, float, bool)) and not hasattr(
                    options, key
                ):
                    setattr(options, key, value)

        options.mode = mode
        options.preview = preview
        digest = int(getattr(self.machine_settings, "digest", 1))
        options.digest = max(0, min(2, digest))
        if preview:
            options.speed_pendown = self._mm_min_to_inch_s(
                self.plot_profile.speed_pendown
            )
            options.speed_penup = self._mm_min_to_inch_s(self.plot_profile.speed_penup)
        else:
            options.speed_pendown = self.plot_profile.speed_pendown
            options.speed_penup = self.plot_profile.speed_penup
        options.accel = self.plot_profile.accel
        # landscape: vendor auto_rotate conflicts with our correction; portrait: needed
        is_landscape_mode = (
            self.machine_settings.table_orientation.strip().lower() == "landscape"
        )
        options.auto_rotate = not is_landscape_mode
        options.reordering = self.plot_profile.reordering
        options.report_time = False
        options.model = get_machine_model(
            self.machine_settings.machine_model
        ).runtime_model
        session._idraw_ui_logical_home_corner = (
            self.machine_settings.my_home_corner.strip().lower()
        )
        session._idraw_ui_table_orientation = (
            self.machine_settings.table_orientation.strip().lower()
        )

        if resume_type is not None:
            options.resume_type = resume_type

        # Use explicit port when provided, otherwise auto-detect first available device.
        options.port = self.machine_settings.port
        options.port_config = 2 if self.machine_settings.port else 1

    @staticmethod
    def _mm_min_to_inch_s(speed_mm_min: float) -> float:
        return float(speed_mm_min) / (25.4 * 60.0)

    def _persist_resume_snapshot(self, session: Any) -> None:
        if not hasattr(session, "get_output"):
            return
        output = session.get_output()
        fd, tmp_path = tempfile.mkstemp(prefix="idraw_resume_", suffix=".svg")
        os.close(fd)
        out_path = Path(tmp_path)
        out_path.write_text(output, encoding="utf-8")
        self._resume_svg_path = out_path

    @staticmethod
    def _extract_metrics(session: Any) -> dict[str, Any]:
        stats = getattr(getattr(session, "plot_status", None), "stats", None)
        if stats is None:
            return {}

        down_in = float(getattr(stats, "down_travel_tot", 0.0)) + float(
            getattr(stats, "down_travel_inch", 0.0)
        )
        up_in = float(getattr(stats, "up_travel_tot", 0.0)) + float(
            getattr(stats, "up_travel_inch", 0.0)
        )

        pen = getattr(session, "pen", None)
        pen_status = getattr(pen, "status", None)
        lifts = int(getattr(pen_status, "lifts", 0))

        pt_estimate_ms = float(getattr(stats, "pt_estimate", 0.0))
        estimated_seconds = pt_estimate_ms / 1000.0 if pt_estimate_ms > 0 else None

        return {
            "estimated_seconds": estimated_seconds,
            "distance_pen_down_mm": down_in * 25.4,
            "distance_total_mm": (down_in + up_in) * 25.4,
            "pen_lifts": lifts,
        }
