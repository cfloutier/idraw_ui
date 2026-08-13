from __future__ import annotations

import pathlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from idraw_ui.backend.idraw2_facade import Idraw2Facade
from idraw_ui.backend.models import PlotState


class FakeRuntime:
    def __init__(self, *, fail_on: str | None = None) -> None:
        self.fail_on = fail_on
        self.calls: list[str] = []
        self.configured = False
        self.status: dict[str, object] = {
            "state": PlotState.IDLE,
            "message": "Idle",
        }

    def _maybe_fail(self, op: str) -> None:
        if self.fail_on == op:
            self.status["state"] = PlotState.IDLE
            self.status["message"] = f"runtime failed {op}"
            raise RuntimeError(f"runtime failed {op}")

    def configure(self, _machine, _profile) -> None:
        self._maybe_fail("configure")
        self.configured = True
        self.calls.append("configure")
        self.status["message"] = "Configured"

    def load_svg(self, _path: Path) -> None:
        self._maybe_fail("load_svg")
        self.calls.append("load_svg")

    def prepare(self) -> dict[str, float]:
        self._maybe_fail("prepare")
        self.calls.append("prepare")
        metrics = {
            "estimated_seconds": 42.5,
            "distance_pen_down_mm": 123.0,
            "distance_total_mm": 245.5,
            "pen_lifts": 7,
        }
        self.status.update(metrics)
        self.status["state"] = PlotState.READY
        self.status["message"] = "Prepared"
        return metrics

    def start(self) -> None:
        self._maybe_fail("start")
        self.calls.append("start")
        self.status["state"] = PlotState.DRAWING
        self.status["message"] = "Drawing"

    def pause(self) -> None:
        self._maybe_fail("pause")
        self.calls.append("pause")
        self.status["state"] = PlotState.PAUSED
        self.status["message"] = "Paused"

    def resume(self) -> None:
        self._maybe_fail("resume")
        self.calls.append("resume")
        self.status["state"] = PlotState.DRAWING
        self.status["message"] = "Resumed"

    def stop(self) -> None:
        self._maybe_fail("stop")
        self.calls.append("stop")
        self.status["state"] = PlotState.READY
        self.status["message"] = "Stopped"

    def home(self) -> None:
        self._maybe_fail("home")
        self.calls.append("home")
        self.status["state"] = PlotState.READY
        self.status["message"] = "Homing completed"

    def get_status(self) -> dict[str, object]:
        return dict(self.status)


class FakeRuntimeNothingToDraw(FakeRuntime):
    """Mirrors the real runtime's `_extract_metrics()` when the digest has no
    plottable content: stats exist, but `estimated_seconds` stays None."""

    def prepare(self) -> dict[str, float | None]:
        self.calls.append("prepare")
        metrics: dict[str, float | None] = {
            "estimated_seconds": None,
            "distance_pen_down_mm": 0.0,
            "distance_total_mm": 0.0,
            "pen_lifts": 0,
        }
        self.status.update(metrics)
        self.status["state"] = PlotState.READY
        self.status["message"] = "Prepared"
        return metrics


class Idraw2FacadeTests(unittest.TestCase):
    def test_runtime_is_configured_on_init(self) -> None:
        runtime = FakeRuntime()
        facade = Idraw2Facade(runtime=runtime)

        self.assertTrue(runtime.configured)
        self.assertIn("configure", runtime.calls)
        self.assertEqual(facade.get_progress().state, PlotState.IDLE)

    def test_default_runtime_factory_is_used(self) -> None:
        runtime = FakeRuntime()

        with patch(
            "idraw_ui.backend.idraw2_facade._default_runtime_factory",
            return_value=runtime,
        ):
            facade = Idraw2Facade()

        self.assertIs(facade.runtime, runtime)
        self.assertTrue(runtime.configured)

    def test_load_svg_requires_existing_file(self) -> None:
        facade = Idraw2Facade(runtime=FakeRuntime())

        result = facade.load_svg("missing.svg")

        self.assertFalse(result.ok)
        self.assertIn("SVG file not found", result.message)

    def test_prepare_updates_progress_metrics(self) -> None:
        runtime = FakeRuntime()
        facade = Idraw2Facade(runtime=runtime)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "input.svg"
            svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")

            self.assertTrue(facade.load_svg(svg_path).ok)
            result = facade.prepare()

        self.assertTrue(result.ok)
        progress = facade.get_progress()
        self.assertEqual(progress.state, PlotState.READY)
        self.assertEqual(progress.estimated_seconds, 42.5)
        self.assertEqual(progress.distance_pen_down_mm, 123.0)
        self.assertEqual(progress.distance_total_mm, 245.5)
        self.assertEqual(progress.pen_lifts, 7)

    def test_prepare_handles_svg_with_nothing_to_draw(self) -> None:
        """Regression test: prepare() must not crash when the runtime reports
        no estimate because the digest has no plottable content (metrics dict
        present but `estimated_seconds` is None)."""
        runtime = FakeRuntimeNothingToDraw()
        facade = Idraw2Facade(runtime=runtime)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "empty.svg"
            svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")

            self.assertTrue(facade.load_svg(svg_path).ok)
            result = facade.prepare()

        self.assertTrue(result.ok)
        progress = facade.get_progress()
        self.assertEqual(progress.state, PlotState.READY)
        self.assertIsNone(progress.estimated_seconds)
        self.assertEqual(progress.distance_pen_down_mm, 0.0)
        self.assertEqual(progress.distance_total_mm, 0.0)
        self.assertEqual(progress.pen_lifts, 0)

    def test_get_progress_refreshes_live_runtime_status(self) -> None:
        runtime = FakeRuntime()
        facade = Idraw2Facade(runtime=runtime)
        runtime.status.update(
            {
                "state": PlotState.DRAWING,
                "message": "Drawing live",
                "elapsed_seconds": 3.5,
                "estimated_seconds": 9.0,
                "distance_pen_down_mm": 11.0,
                "distance_total_mm": 21.0,
                "pen_lifts": 2,
            }
        )

        progress = facade.get_progress()

        self.assertEqual(progress.state, PlotState.DRAWING)
        self.assertEqual(progress.message, "Drawing live")
        self.assertEqual(progress.elapsed_seconds, 3.5)
        self.assertEqual(progress.estimated_seconds, 9.0)
        self.assertEqual(progress.distance_pen_down_mm, 11.0)
        self.assertEqual(progress.distance_total_mm, 21.0)
        self.assertEqual(progress.pen_lifts, 2)

    def test_start_auto_prepares_when_needed(self) -> None:
        runtime = FakeRuntime()
        facade = Idraw2Facade(runtime=runtime)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "input.svg"
            svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")
            self.assertTrue(facade.load_svg(svg_path).ok)

            result = facade.start()

        self.assertTrue(result.ok)
        self.assertEqual(facade.get_progress().state, PlotState.DRAWING)
        self.assertIn("prepare", runtime.calls)
        self.assertIn("start", runtime.calls)

    def test_reconfigure_invalidates_prepared_svg(self) -> None:
        runtime = FakeRuntime()
        facade = Idraw2Facade(runtime=runtime)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "input.svg"
            svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")
            self.assertTrue(facade.load_svg(svg_path).ok)
            self.assertTrue(facade.prepare().ok)
            prepare_count = runtime.calls.count("prepare")

            facade.reconfigure(machine_settings=facade.machine_settings)
            self.assertTrue(facade.start().ok)

        self.assertEqual(runtime.calls.count("prepare"), prepare_count + 1)

    def test_pause_resume_transitions(self) -> None:
        runtime = FakeRuntime()
        facade = Idraw2Facade(runtime=runtime)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "input.svg"
            svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")
            self.assertTrue(facade.load_svg(svg_path).ok)
            self.assertTrue(facade.start().ok)

        paused = facade.pause()
        resumed = facade.resume()

        self.assertTrue(paused.ok)
        self.assertTrue(resumed.ok)
        self.assertEqual(facade.get_progress().state, PlotState.DRAWING)
        self.assertIn("pause", runtime.calls)
        self.assertIn("resume", runtime.calls)

    def test_runtime_failure_is_reported(self) -> None:
        runtime = FakeRuntime(fail_on="start")
        facade = Idraw2Facade(runtime=runtime)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "input.svg"
            svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")
            self.assertTrue(facade.load_svg(svg_path).ok)
            result = facade.start()

        self.assertFalse(result.ok)
        self.assertIn("runtime failed start", result.message)
        self.assertEqual(facade.get_progress().state, PlotState.IDLE)


if __name__ == "__main__":
    unittest.main()
