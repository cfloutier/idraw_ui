from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from idraw_ui.backend.models import AppState, MachineSettings, PlotProfile
from idraw_ui.backend.profiles import (
    app_state_from_mapping,
    machine_settings_from_mapping,
    plot_profile_from_mapping,
)


class SettingsService:
    """Persistent settings and profile manager for the UI application."""

    def __init__(self, root_dir: str | Path | None = None) -> None:
        self.root_dir = Path(root_dir or self._default_root_dir()).resolve()
        self.settings_dir = self.root_dir / "settings"
        self.profiles_dir = self.root_dir / "profiles"
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        self.machine_settings = self.load_machine_settings()
        self.app_state = self.load_app_state()
        self._ensure_default_profile_exists()

    @staticmethod
    def _default_root_dir() -> Path:
        return Path(__file__).resolve().parents[3]

    def _settings_path(self, name: str) -> Path:
        return self.settings_dir / f"{name}.yaml"

    def _profile_path(self, profile_name: str) -> Path:
        return self.profiles_dir / f"{profile_name}.yaml"

    def _load_mapping(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        raw_text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw_text) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Settings file must contain a mapping: {path}")
        return data

    def load_machine_settings(self) -> MachineSettings:
        path = self._settings_path("machine")
        if not path.exists():
            return MachineSettings()
        return machine_settings_from_mapping(self._load_mapping(path))

    def save_machine_settings(self, machine_settings: MachineSettings) -> None:
        self.machine_settings = machine_settings
        self._write_yaml(self._settings_path("machine"), asdict(machine_settings))

    def load_app_state(self) -> AppState:
        path = self._settings_path("app_state")
        if not path.exists():
            return AppState()
        return app_state_from_mapping(self._load_mapping(path))

    def save_app_state(self, app_state: AppState | None = None) -> AppState:
        active_state = app_state or self.app_state
        self.app_state = active_state
        self._write_yaml(self._settings_path("app_state"), asdict(active_state))
        return self.app_state

    def list_profile_names(self) -> list[str]:
        if not self.profiles_dir.exists():
            return []
        names = []
        for path in sorted(self.profiles_dir.glob("*.yaml")):
            if path.stem == "default" or path.stem != "app_state":
                names.append(path.stem)
        return names

    def load_profile(self, profile_name: str | None = None) -> PlotProfile:
        name = profile_name or self.app_state.active_profile or "default"
        path = self._profile_path(name)
        if not path.exists():
            return PlotProfile(name=name)
        return plot_profile_from_mapping(self._load_mapping(path))

    def save_profile(self, profile: PlotProfile) -> PlotProfile:
        path = self._profile_path(profile.name or "default")
        self._write_yaml(path, asdict(profile))
        return profile

    def set_active_profile(self, profile_name: str) -> PlotProfile:
        self.app_state.active_profile = profile_name
        self.save_app_state(self.app_state)
        return self.load_profile(profile_name)

    def create_profile(
        self, profile_name: str, source_profile: PlotProfile | None = None
    ) -> PlotProfile:
        base_profile = source_profile or self.load_profile(
            self.app_state.active_profile
        )
        new_profile = PlotProfile(**{**asdict(base_profile), "name": profile_name})
        self.save_profile(new_profile)
        self.set_active_profile(profile_name)
        return new_profile

    def _ensure_default_profile_exists(self) -> None:
        if "default" not in self.list_profile_names():
            self.save_profile(PlotProfile(name="default"))

    def _write_yaml(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
