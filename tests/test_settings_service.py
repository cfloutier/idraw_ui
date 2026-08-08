from __future__ import annotations

from pathlib import Path

import yaml

from idraw_ui.backend.driver import Driver
from idraw_ui.backend.models import MachineSettings, PlotProfile
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


def test_app_state_persists_jog_mode(tmp_path: Path) -> None:
    service = SettingsService(root_dir=tmp_path)

    service.app_state.jog_mode = "table"
    service.save_app_state()

    reloaded = SettingsService(root_dir=tmp_path)
    assert reloaded.app_state.jog_mode == "table"

    state_path = tmp_path / "settings" / "app_state.yaml"
    payload = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    assert payload["jog_mode"] == "table"


def test_app_state_persists_last_svg_file_and_folder(tmp_path: Path) -> None:
    service = SettingsService(root_dir=tmp_path)

    svg_path = tmp_path / "samples" / "drawing.svg"
    service.app_state.last_svg_file = str(svg_path)
    service.app_state.last_folder = str(svg_path.parent)
    service.save_app_state()

    reloaded = SettingsService(root_dir=tmp_path)
    assert reloaded.app_state.last_svg_file == str(svg_path)
    assert reloaded.app_state.last_folder == str(svg_path.parent)

    state_path = tmp_path / "settings" / "app_state.yaml"
    payload = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    assert payload["last_svg_file"] == str(svg_path)
    assert payload["last_folder"] == str(svg_path.parent)


def test_machine_settings_persist_selected_model(tmp_path: Path) -> None:
    service = SettingsService(root_dir=tmp_path)

    machine_settings = MachineSettings(
        machine_model="idraw-a3",
        table_orientation="portrait",
        drawing_margin_top_mm=11,
        drawing_margin_bottom_mm=22,
        drawing_margin_left_mm=33,
        drawing_margin_right_mm=44,
        digest=2,
    )
    service.save_machine_settings(machine_settings)

    reloaded = SettingsService(root_dir=tmp_path)
    assert reloaded.machine_settings.machine_model == "idraw-a3"
    assert reloaded.machine_settings.table_orientation == "portrait"
    assert reloaded.machine_settings.drawing_margin_top_mm == 11
    assert reloaded.machine_settings.drawing_margin_bottom_mm == 22
    assert reloaded.machine_settings.drawing_margin_left_mm == 33
    assert reloaded.machine_settings.drawing_margin_right_mm == 44
    assert reloaded.machine_settings.digest == 2

    machine_path = tmp_path / "settings" / "machine.yaml"
    payload = yaml.safe_load(machine_path.read_text(encoding="utf-8"))
    assert payload["machine_model"] == "idraw-a3"
    assert payload["table_orientation"] == "portrait"
    assert payload["drawing_margin_top_mm"] == 11
    assert payload["drawing_margin_bottom_mm"] == 22
    assert payload["drawing_margin_left_mm"] == 33
    assert payload["drawing_margin_right_mm"] == 44
    assert "my_home_padding_mm" not in payload
    assert payload["digest"] == 2


def test_legacy_home_padding_migrates_to_four_drawing_margins(tmp_path: Path) -> None:
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir(parents=True)
    (settings_dir / "machine.yaml").write_text(
        "machine_model: idraw-a2\nmy_home_padding_mm: 17.6\n",
        encoding="utf-8",
    )

    settings = SettingsService(root_dir=tmp_path).machine_settings

    assert settings.drawing_margin_top_mm == 18
    assert settings.drawing_margin_bottom_mm == 18
    assert settings.drawing_margin_left_mm == 18
    assert settings.drawing_margin_right_mm == 18
