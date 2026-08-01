from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from idraw_ui.backend.models import MachineProfile


_MACHINE_PROFILE_KEYS = {
    "name",
    "machine_model",
    "pen_up_height",
    "pen_down_height",
    "speed_penup",
    "speed_pendown",
    "accel",
    "auto_rotate",
    "reordering",
    "preview",
    "digest",
}


def machine_profile_from_mapping(data: Mapping[str, Any]) -> MachineProfile:
    profile_kwargs: dict[str, Any] = {}
    extra_fields: dict[str, Any] = {}

    for key, value in data.items():
        if key in _MACHINE_PROFILE_KEYS:
            profile_kwargs[key] = value
        else:
            extra_fields[key] = value

    profile = MachineProfile(**profile_kwargs)
    profile.field.update(extra_fields)
    return profile


def load_machine_profile(path: str | Path) -> MachineProfile:
    profile_path = Path(path)
    raw_text = profile_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw_text) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Profile file must contain a mapping: {profile_path}")

    return machine_profile_from_mapping(data)
