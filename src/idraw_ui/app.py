from __future__ import annotations

from pathlib import Path

from idraw_ui.backend.driver import Driver
from idraw_ui.backend.settings_service import SettingsService
from idraw_ui.ui.app_window import AppWindow


def main() -> None:
    """Start the MVP UI wired to backend driver controls."""

    project_root = Path(__file__).resolve().parents[2]
    settings_service = SettingsService(root_dir=project_root)

    machine_settings = settings_service.load_machine_settings()
    app_state = settings_service.load_app_state()
    default_profile = settings_service.load_profile(app_state.active_profile)

    driver = Driver(
        machine_settings=machine_settings,
        plot_profile=default_profile,
    )

    window = AppWindow(driver, settings_service=settings_service)
    window.show()


if __name__ == "__main__":
    main()
