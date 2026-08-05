from __future__ import annotations

import pathlib
import sys
import tempfile
import time
import unittest
from dataclasses import replace
from types import SimpleNamespace

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from idraw_ui.backend.idraw2_runtime import Idraw2InternalRuntime  # noqa: E402


class FakeSession:
    def __init__(self, *, wait_for_pause: bool = False) -> None:
        self.wait_for_pause = wait_for_pause
        self.pause_event = None
        self.options = SimpleNamespace()
        self.document = None
        self.original_document = None
        self.plot_status = SimpleNamespace(
            stats=SimpleNamespace(
                down_travel_tot=1.0,
                down_travel_inch=0.5,
                up_travel_tot=0.75,
                up_travel_inch=0.25,
                pt_estimate=12000,
            ),
            stopped=0,
        )
        self.pen = SimpleNamespace(status=SimpleNamespace(lifts=3))

    def getoptions(self, _args: list[str]) -> None:
        return

    def set_up_pause_receiver(self, pause_event) -> None:
        self.pause_event = pause_event

    def effect(self) -> None:
        if self.wait_for_pause and self.pause_event is not None:
            deadline = time.time() + 1.0
            while not self.pause_event.is_set() and time.time() < deadline:
                time.sleep(0.01)
            self.plot_status.stopped = 103

    def get_output(self) -> str:
        return "<svg xmlns='http://www.w3.org/2000/svg'><plotdata /></svg>"


class FakeSessionFactory:
    def __init__(self, *, wait_for_pause: bool = False) -> None:
        self.wait_for_pause = wait_for_pause
        self.sessions: list[FakeSession] = []

    def __call__(self) -> FakeSession:
        session = FakeSession(wait_for_pause=self.wait_for_pause)
        self.sessions.append(session)
        return session


class Idraw2InternalRuntimeTests(unittest.TestCase):
    def test_prepare_collects_metrics(self) -> None:
        factory = FakeSessionFactory()
        runtime = Idraw2InternalRuntime(session_factory=factory)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "input.svg"
            svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")

            runtime.load_svg(svg_path)
            metrics = runtime.prepare()

        self.assertIsNotNone(metrics)
        assert metrics is not None
        self.assertEqual(metrics["pen_lifts"], 3)
        self.assertEqual(metrics["estimated_seconds"], 12.0)
        self.assertGreater(metrics["distance_pen_down_mm"], 0.0)
        self.assertGreater(
            metrics["distance_total_mm"], metrics["distance_pen_down_mm"]
        )

    def test_start_and_pause_cycle(self) -> None:
        factory = FakeSessionFactory(wait_for_pause=True)
        runtime = Idraw2InternalRuntime(session_factory=factory)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "input.svg"
            svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")

            runtime.load_svg(svg_path)
            runtime.start()
            running_status = runtime.get_status()
            runtime.pause()
            paused_status = runtime.get_status()

        self.assertGreaterEqual(len(factory.sessions), 1)
        self.assertEqual(factory.sessions[-1].plot_status.stopped, 103)
        self.assertEqual(running_status["state"], "drawing")
        self.assertEqual(paused_status["state"], "paused")
        self.assertEqual(paused_status["message"], "Paused")

    def test_resume_uses_resume_mode(self) -> None:
        factory = FakeSessionFactory(wait_for_pause=True)
        runtime = Idraw2InternalRuntime(session_factory=factory)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "input.svg"
            svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")

            runtime.load_svg(svg_path)
            runtime.start()
            runtime.pause()
            runtime.resume()
            runtime.stop()

        self.assertGreaterEqual(len(factory.sessions), 2)
        # Session created by resume() must receive resume mode.
        self.assertEqual(factory.sessions[-1].options.mode, "resume")
        self.assertEqual(factory.sessions[-1].options.resume_type, "plot")

    def test_home_uses_resume_home_mode(self) -> None:
        factory = FakeSessionFactory()
        runtime = Idraw2InternalRuntime(session_factory=factory)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "input.svg"
            svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")

            runtime.load_svg(svg_path)
            runtime.prepare()
            runtime.home()

        self.assertGreaterEqual(len(factory.sessions), 2)
        self.assertEqual(factory.sessions[-1].options.mode, "resume")
        self.assertEqual(factory.sessions[-1].options.resume_type, "home")

    def test_stop_reports_ready_state(self) -> None:
        factory = FakeSessionFactory(wait_for_pause=True)
        runtime = Idraw2InternalRuntime(session_factory=factory)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "input.svg"
            svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")

            runtime.load_svg(svg_path)
            runtime.start()
            runtime.stop()

        status = runtime.get_status()
        self.assertEqual(status["state"], "ready")
        self.assertEqual(status["message"], "Stopped")

    def test_prepare_uses_converted_speeds_for_estimate_only(self) -> None:
        factory = FakeSessionFactory()
        runtime = Idraw2InternalRuntime(session_factory=factory)
        runtime.plot_profile = replace(
            runtime.plot_profile,
            speed_penup=8000.0,
            speed_pendown=2000.0,
            accel=75.0,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "input.svg"
            svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")

            runtime.load_svg(svg_path)
            runtime.prepare()

        self.assertGreaterEqual(len(factory.sessions), 1)
        session = factory.sessions[-1]
        self.assertTrue(session.options.preview)
        self.assertAlmostEqual(session.options.speed_penup, 8000.0 / (25.4 * 60.0))
        self.assertAlmostEqual(session.options.speed_pendown, 2000.0 / (25.4 * 60.0))

    def test_start_keeps_raw_speeds_for_real_plot(self) -> None:
        factory = FakeSessionFactory(wait_for_pause=True)
        runtime = Idraw2InternalRuntime(session_factory=factory)
        runtime.plot_profile = replace(
            runtime.plot_profile,
            speed_penup=8000.0,
            speed_pendown=2000.0,
            accel=75.0,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "input.svg"
            svg_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")

            runtime.load_svg(svg_path)
            runtime.start()
            runtime.stop()

        self.assertGreaterEqual(len(factory.sessions), 1)
        session = factory.sessions[-1]
        self.assertFalse(session.options.preview)
        self.assertEqual(session.options.speed_penup, 8000.0)
        self.assertEqual(session.options.speed_pendown, 2000.0)


if __name__ == "__main__":
    unittest.main()
