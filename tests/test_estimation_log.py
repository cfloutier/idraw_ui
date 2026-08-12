from __future__ import annotations

import csv
import pathlib
import tempfile
import unittest

from idraw_ui.backend.estimation_log import (
    CalibrationRow,
    append_calibration_row,
    default_calibration_log_path,
)


def _row(**overrides: object) -> CalibrationRow:
    defaults = dict(
        svg_name="test.svg",
        estimated_seconds=12.0,
        actual_seconds=20.0,
        pen_lifts=3,
        distance_pen_down_mm=100.0,
        distance_total_mm=150.0,
        speed_penup=8000.0,
        speed_pendown=2000.0,
        accel=75.0,
        pen_up_height=0.5,
        pen_down_height=5.0,
        machine_model="idraw-a1",
        table_orientation="landscape",
        digest=1,
    )
    defaults.update(overrides)
    return CalibrationRow(**defaults)


class AppendCalibrationRowTests(unittest.TestCase):
    def test_creates_file_with_header_and_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = pathlib.Path(tmp_dir) / "nested" / "calibration.csv"

            append_calibration_row(path, _row())

            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["svg_name"], "test.svg")
        self.assertEqual(rows[0]["estimated_seconds"], "12.0")
        self.assertEqual(rows[0]["actual_seconds"], "20.0")
        self.assertEqual(rows[0]["pen_lifts"], "3")
        self.assertIn("timestamp", rows[0])
        self.assertTrue(rows[0]["timestamp"])

    def test_appends_without_duplicating_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = pathlib.Path(tmp_dir) / "calibration.csv"

            append_calibration_row(path, _row(svg_name="first.svg"))
            append_calibration_row(path, _row(svg_name="second.svg"))

            with path.open(encoding="utf-8") as handle:
                lines = handle.readlines()
                handle.seek(0)
                rows = list(csv.DictReader(handle))

        header_lines = [line for line in lines if line.startswith("timestamp,")]
        self.assertEqual(len(header_lines), 1)
        self.assertEqual(len(rows), 2)
        self.assertEqual([row["svg_name"] for row in rows], ["first.svg", "second.svg"])

    def test_handles_none_estimated_seconds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = pathlib.Path(tmp_dir) / "calibration.csv"

            append_calibration_row(path, _row(estimated_seconds=None))

            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(rows[0]["estimated_seconds"], "")


class DefaultCalibrationLogPathTests(unittest.TestCase):
    def test_points_under_project_root_logs_dir(self) -> None:
        path = default_calibration_log_path()

        self.assertEqual(path.name, "time_estimation_calibration.csv")
        self.assertEqual(path.parent.name, "logs")


if __name__ == "__main__":
    unittest.main()
