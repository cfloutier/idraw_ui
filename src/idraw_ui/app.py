from __future__ import annotations

from pathlib import Path

from idraw_ui.backend.driver import Driver
from idraw_ui.ui.app_window import AppWindow


def main() -> None:
    """Start the MVP UI wired to backend driver controls."""

    project_root = Path(__file__).resolve().parents[2]
    machine_settings = project_root / "settings" / "machine.yaml"
    default_profile = project_root / "profiles" / "default.yaml"

    if machine_settings.exists() and default_profile.exists():
        driver = Driver.from_config_files(machine_settings, default_profile)
    else:
        driver = Driver()

    window = AppWindow(driver)
    window.show()


if __name__ == "__main__":
    main()
