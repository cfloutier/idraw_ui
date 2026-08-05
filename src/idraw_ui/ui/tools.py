from __future__ import annotations


def format_float(value: float) -> str:
    if value >= 100:
        return f"{value:.0f}"
    if value >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "-"

    total_seconds = max(0, int(round(seconds)))
    days, day_remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(day_remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    if days > 0:
        return f"{days:d}d {hours:02d}h {minutes:02d}m {secs:02d}s"
    if hours > 0:
        return f"{hours:d}h {minutes:02d}m {secs:02d}s"
    if minutes > 0:
        return f"{minutes:d}m {secs:02d}s"
    return f"{secs:d}s"


def format_distance_mm(value_mm: float) -> str:
    if value_mm >= 10.0:
        return f"{format_float(value_mm / 10.0)} cm"
    return f"{format_float(value_mm)} mm"


def _mm_min_to_inch_s(speed_mm_min: float) -> float:
    return float(speed_mm_min) / (25.4 * 60.0)
