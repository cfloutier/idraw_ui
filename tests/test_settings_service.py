from __future__ import annotations

from pathlib import Path

import yaml

from idraw_ui.backend.driver import Driver
from idraw_ui.backend.models import PlotProfile
from idraw_ui.backend.settings_service import SettingsService


def test_driver_notifies_profile_change_listeners() -> None:
    driver = Driver(plot_profile=PlotProfile(name="default", pen_up_height=1.0))
    notified: list[PlotProfile] = []

    driver.add_profile_change_listener(notified.append)
    driver.update_plot_profile(name="updated", pen_up_height=2.5)

    assert len(notified) == 1
    assert notified[0].name == "updated"
    assert notified[0].pen_up_height == 2.5


def test_profile_persistence_and_active_profile(tmp_path: Path) -> None:
    service = SettingsService(root_dir=tmp_path)

    profile = PlotProfile(name="default", pen_up_height=1.25, pen_down_height=4.5)
    service.save_profile(profile)

    assert service.list_profile_names() == ["default"]
    loaded = service.load_profile("default")
    assert loaded.name == "default"
    assert loaded.pen_up_height == 1.25
    assert loaded.pen_down_height == 4.5

    service.set_active_profile("default")
    assert service.app_state.active_profile == "default"

    created = service.create_profile("test_profile", source_profile=profile)
    assert created.name == "test_profile"
    assert service.load_profile("test_profile").pen_up_height == 1.25

    state_path = tmp_path / "settings" / "app_state.yaml"
    assert state_path.exists()
    payload = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    assert payload["active_profile"] == "test_profile"


def test_app_state_persists_active_tab(tmp_path: Path) -> None:
    service = SettingsService(root_dir=tmp_path)

    service.app_state.active_tab = "Jog"
    service.save_app_state()

    reloaded = SettingsService(root_dir=tmp_path)
    assert reloaded.app_state.active_tab == "Jog"

    state_path = tmp_path / "settings" / "app_state.yaml"
    payload = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    assert payload["active_tab"] == "Jog"


def test_app_state_persists_jog_distance(tmp_path: Path) -> None:
    service = SettingsService(root_dir=tmp_path)

    service.app_state.jog_distance_mm = 37.0
    service.save_app_state()

    reloaded = SettingsService(root_dir=tmp_path)
    assert reloaded.app_state.jog_distance_mm == 37.0

    state_path = tmp_path / "settings" / "app_state.yaml"
    payload = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    assert payload["jog_distance_mm"] == 37.0
