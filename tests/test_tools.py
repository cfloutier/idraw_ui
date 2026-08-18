from __future__ import annotations

from idraw_ui.ui.tools import format_distance_mm, format_int_thousands


def test_format_distance_mm_millimeters() -> None:
    assert format_distance_mm(0.5) == "0.50 mm"
    assert format_distance_mm(9.9) == "9.90 mm"


def test_format_distance_mm_centimeters() -> None:
    assert format_distance_mm(10.0) == "1.00 cm"
    assert format_distance_mm(66.0) == "6.60 cm"
    assert format_distance_mm(999.0) == "99.9 cm"


def test_format_distance_mm_meters() -> None:
    assert format_distance_mm(1_000.0) == "1.000 m"
    assert format_distance_mm(66_413.0) == "66.413 m"
    assert format_distance_mm(999_999.0) == "999.999 m"


def test_format_distance_mm_kilometers() -> None:
    assert format_distance_mm(1_000_000.0) == "1.000 km"
    assert format_distance_mm(2_345_678.0) == "2.346 km"


def test_format_int_thousands() -> None:
    assert format_int_thousands(0) == "0"
    assert format_int_thousands(151) == "151"
    assert format_int_thousands(19266) == "19 266"
    assert format_int_thousands(1234567) == "1 234 567"
