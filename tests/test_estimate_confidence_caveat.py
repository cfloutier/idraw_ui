from __future__ import annotations

from idraw_ui.backend.models import PlotProgress
from idraw_ui.ui.app_window import AppWindow


def _progress(pen_lifts: int, distance_pen_down_mm: float, distance_total_mm: float) -> PlotProgress:
    return PlotProgress(
        pen_lifts=pen_lifts,
        distance_pen_down_mm=distance_pen_down_mm,
        distance_total_mm=distance_total_mm,
    )


def test_no_caveat_for_few_pen_lifts() -> None:
    # 08_single_long_pen_up_hop.svg: 3 lifts, one very long hop - accurate in calibration.
    progress = _progress(pen_lifts=3, distance_pen_down_mm=8.0, distance_total_mm=1272.5)
    assert AppWindow._estimate_confidence_caveat(progress) is None


def test_no_caveat_for_many_lifts_with_short_hops() -> None:
    # 07_pure_pen_lifts_stationary.svg: 301 lifts but ~4.7 mm avg hop - accurate in calibration.
    progress = _progress(pen_lifts=301, distance_pen_down_mm=300.0, distance_total_mm=1709.0)
    assert AppWindow._estimate_confidence_caveat(progress) is None


def test_caveat_for_many_lifts_with_long_hops() -> None:
    # 03_many_pen_lifts.svg: 151 lifts, ~43 mm avg hop - 28% optimistic in calibration.
    progress = _progress(pen_lifts=151, distance_pen_down_mm=600.0, distance_total_mm=7113.2)
    caveat = AppWindow._estimate_confidence_caveat(progress)
    assert caveat is not None
    assert "optimistic" in caveat


def test_caveat_for_many_lifts_with_very_long_hops() -> None:
    # 06_many_pen_lifts_long_hops.svg: 151 lifts, ~124 mm avg hop - 22-27% optimistic in calibration.
    progress = _progress(pen_lifts=151, distance_pen_down_mm=600.0, distance_total_mm=19385.7)
    assert AppWindow._estimate_confidence_caveat(progress) is not None


def test_no_caveat_at_zero_lifts() -> None:
    progress = _progress(pen_lifts=0, distance_pen_down_mm=100.0, distance_total_mm=100.0)
    assert AppWindow._estimate_confidence_caveat(progress) is None
