from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from idraw_ui.backend.models import AppState, MachineSettings, PlotProfile


_MACHINE_SETTINGS_KEYS = {
    "name",
    "machine_model",
    "port",
    "baudrate",
    "serial_timeout",
}

_PLOT_PROFILE_KEYS = {
    "name",
    "pen_up_height",
    "pen_down_height",
    "pen_move_speed",
    "speed_penup",
    "speed_pendown",
    "accel",
    "auto_rotate",
    "reordering",
    "preview",
    "digest",
    "pen_up_command",
    "pen_down_command",
}

_APP_STATE_KEYS = {
    "active_profile",
    "active_tab",
    "jog_distance_mm",
    "last_svg_file",
    "last_folder",
}


def _load_yaml_mapping(path: str | Path) -> Mapping[str, Any]:
    profile_path = Path(path)
    raw_text = profile_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw_text) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Profile file must contain a mapping: {profile_path}")

    return data


def _split_known_keys(
    data: Mapping[str, Any],
    allowed_keys: set[str],
    *,
    kind: str,
) -> dict[str, Any]:
    unknown = sorted(key for key in data.keys() if key not in allowed_keys)
    if unknown:
        raise ValueError(f"Unknown {kind} keys: {', '.join(unknown)}")
    return {key: value for key, value in data.items() if key in allowed_keys}


def machine_settings_from_mapping(data: Mapping[str, Any]) -> MachineSettings:
    values = _split_known_keys(data, _MACHINE_SETTINGS_KEYS, kind="machine settings")
    return MachineSettings(**values)


def plot_profile_from_mapping(data: Mapping[str, Any]) -> PlotProfile:
    values = _split_known_keys(data, _PLOT_PROFILE_KEYS, kind="plot profile")
    return PlotProfile(**values)


def app_state_from_mapping(data: Mapping[str, Any]) -> AppState:
    values = _split_known_keys(data, _APP_STATE_KEYS, kind="app state")
    return AppState(**values)


def load_machine_settings(path: str | Path) -> MachineSettings:
    return machine_settings_from_mapping(_load_yaml_mapping(path))


def load_plot_profile(path: str | Path) -> PlotProfile:
    return plot_profile_from_mapping(_load_yaml_mapping(path))


def load_app_state(path: str | Path) -> AppState:
    return app_state_from_mapping(_load_yaml_mapping(path))
