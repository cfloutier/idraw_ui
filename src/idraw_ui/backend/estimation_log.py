from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class CalibrationRow:
    """One real (non-preview) plot's estimated-vs-actual timing, plus the
    drawing/profile metadata needed to analyze the gap across many plots."""

    svg_name: str
    estimated_seconds: float | None
    actual_seconds: float
    pen_lifts: int
    distance_pen_down_mm: float
    distance_total_mm: float
    speed_penup: float
    speed_pendown: float
    accel: float
    pen_up_height: float
    pen_down_height: float
    machine_model: str
    table_orientation: str
    digest: int


_FIELDNAMES = ["timestamp", *(f.name for f in fields(CalibrationRow))]


def default_calibration_log_path() -> Path:
    """Project-root-relative default location, matching SettingsService's
    convention for finding the root regardless of the process's cwd."""
    root_dir = Path(__file__).resolve().parents[3]
    return root_dir / "logs" / "time_estimation_calibration.csv"


def append_calibration_row(path: str | Path, row: CalibrationRow) -> None:
    """Append one row to the time-estimation calibration CSV at `path`.

    Creates the parent directory and writes the header first if the file
    doesn't exist yet (or is empty).
    """
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    is_new_file = not csv_path.exists() or csv_path.stat().st_size == 0

    with csv_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_FIELDNAMES)
        if is_new_file:
            writer.writeheader()
        writer.writerow({"timestamp": datetime.now().isoformat(timespec="seconds"), **asdict(row)})
