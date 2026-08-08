from __future__ import annotations

import pathlib
import tempfile
import time
import unittest
from dataclasses import replace
from types import SimpleNamespace

from idraw_ui.backend.idraw2_runtime import (
    Idraw2InternalRuntime,
    _apply_logical_home_to_digest,
)


class FakeDigest:
    def __init__(self) -> None:
        self.width = 4.0
        self.height = 3.0
        self.metadata: dict[str, str] = {}
        path = SimpleNamespace(subpaths=[[[0.5, 0.25], [1.5, 2.25]]])
        self.layers = [SimpleNamespace(paths=[path])]


def _logical_home_session() -> SimpleNamespace:
    return SimpleNamespace(
        digest=FakeDigest(),
        params=SimpleNamespace(start_pos_x=0.0, start_pos_y=0.0),
        pen=SimpleNamespace(phys=SimpleNamespace(xpos=0.0, ypos=0.0)),
        options=SimpleNamespace(digest=0),
    )


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
    def test_logical_home_transform_preserves_content_orientation(self) -> None:
        expected = {
            "bottom-right": ([[3.5, 2.75], [2.5, 0.75]], (0.0, 3.0)),
            "bottom-left": ([[3.5, 2.75], [2.5, 0.75]], (0.0, 0.0)),
            "top-right": ([[3.5, 2.75], [2.5, 0.75]], (4.0, 3.0)),
            "top-left": ([[3.5, 2.75], [2.5, 0.75]], (4.0, 0.0)),
        }

        for home_corner, (expected_vertices, expected_start) in expected.items():
            with self.subTest(home_corner=home_corner):
                session = _logical_home_session()

                _apply_logical_home_to_digest(session, home_corner)

                vertices = session.digest.layers[0].paths[0].subpaths[0]
                self.assertEqual(vertices, expected_vertices)
                self.assertEqual(
                    (session.params.start_pos_x, session.params.start_pos_y),
                    expected_start,
                )
                self.assertEqual(
                    (session.pen.phys.xpos, session.pen.phys.ypos),
                    expected_start,
                )

    def test_logical_home_transform_is_idempotent_for_resume_digest(self) -> None:
        session = _logical_home_session()

        _apply_logical_home_to_digest(session, "top-left")
        first_vertices = [
            vertex.copy() for vertex in session.digest.layers[0].paths[0].subpaths[0]
        ]
        _apply_logical_home_to_digest(session, "top-left")

        self.assertEqual(
            session.digest.layers[0].paths[0].subpaths[0],
            first_vertices,
        )

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

    def test_start_after_prepare_uses_original_svg(self) -> None:
        factory = FakeSessionFactory()
        runtime = Idraw2InternalRuntime(session_factory=factory)

        with tempfile.TemporaryDirectory() as tmp_dir:
            svg_path = pathlib.Path(tmp_dir) / "input.svg"
            svg_path.write_text(
                "<svg xmlns='http://www.w3.org/2000/svg' id='source'></svg>"
            )

            runtime.load_svg(svg_path)
            runtime.prepare()
            runtime.start()
            while runtime._thread_running():
                time.sleep(0.01)

        self.assertGreaterEqual(len(factory.sessions), 2)
        started_document = factory.sessions[-1].document
        self.assertEqual(started_document.getroot().get("id"), "source")

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
