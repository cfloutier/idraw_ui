from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from idraw_ui.backend.idraw2_facade import Idraw2Facade  # noqa: E402
from idraw_ui.backend.models import PlotState  # noqa: E402


class FakeRuntime:
    def __init__(self, *, fail_on: str | None = None) -> None:
        self.fail_on = fail_on
        self.calls: list[str] = []
        self.configured = False

    def _maybe_fail(self, op: str) -> None:
        if self.fail_on == op:
            raise RuntimeError(f"runtime failed {op}")

    def configure(self, _machine, _profile) -> None:
        self._maybe_fail("configure")
        self.configured = True
        self.calls.append("configure")

    def load_svg(self, _path: Path) -> None:
        self._maybe_fail("load_svg")
        self.calls.append("load_svg")

    def prepare(self) -> dict[str, float]:
        self._maybe_fail("prepare")
        self.calls.append("prepare")
        return {
            "estimated_seconds": 42.5,
            "distance_pen_down_mm": 123.0,
            "distance_total_mm": 245.5,
            "pen_lifts": 7,
        }

    def start(self) -> None:
        self._maybe_fail("start")
        self.calls.append("start")

    def pause(self) -> None:
        self._maybe_fail("pause")
        self.calls.append("pause")

    def resume(self) -> None:
        self._maybe_fail("resume")
        self.calls.append("resume")

    def stop(self) -> None:
        self._maybe_fail("stop")
        self.calls.append("stop")

    def home(self) -> None:
        self._maybe_fail("home")
        self.calls.append("home")


class Idraw2FacadeTests(unittest.TestCase):
    def test_runtime_is_configured_on_init(self) -> None:
        runtime = FakeRuntime()
        facade = Idraw2Facade(runtime=runtime)

        self.assertTrue(runtime.configured)
        self.assertIn("configure", runtime.calls)
        self.assertEqual(facade.get_progress().state, PlotState.IDLE)

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
