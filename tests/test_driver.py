from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest
import yaml

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from idraw_ui.backend.driver import Driver  # noqa: E402
from idraw_ui.backend.profiles import (  # noqa: E402
    load_app_state,
    load_machine_settings,
    load_plot_profile,
)
from idraw_ui.backend.vendor_bridge import VendorBridgeError  # noqa: E402


class FakeBridge:
    def __init__(
        self,
        *,
        fail_on: str | None = None,
        fail_with_runtime_on: str | None = None,
    ) -> None:
        self.fail_on = fail_on
        self.fail_with_runtime_on = fail_with_runtime_on
        self.connected = False

    def _maybe_fail(self, op: str) -> None:
        if self.fail_with_runtime_on == op:
            raise RuntimeError(f"runtime failed {op}")
        if self.fail_on == op:
            raise VendorBridgeError(f"failed {op}")

    def connect(self) -> bool:
        self._maybe_fail("connect")
        self.connected = True
        return True

    def disconnect(self) -> None:
        self._maybe_fail("disconnect")
        self.connected = False

    def get_status(self) -> str:
        self._maybe_fail("status")
        return "<Idle|MPos:0.000,0.000,0.000>"

    def home(self) -> str:
        self._maybe_fail("home")
        return "ok"

    def raise_pen(self) -> str:
        self._maybe_fail("raise_pen")
        return "ok"

    def lower_pen(self) -> str:
        self._maybe_fail("lower_pen")
        return "ok"


class DriverTests(unittest.TestCase):
    def test_connect_success(self) -> None:
        driver = Driver(bridge=FakeBridge())
        result = driver.connect()
        self.assertTrue(result.ok)
        self.assertIn("connected", result.message)

    def test_home_failure_propagates(self) -> None:
        driver = Driver(bridge=FakeBridge(fail_on="home"))
        driver.connect()
        result = driver.home()
        self.assertFalse(result.ok)
        self.assertIn("failed home", result.message)

    def test_pen_actions_success(self) -> None:
        driver = Driver(bridge=FakeBridge())
        driver.connect()
        self.assertTrue(driver.raise_pen().ok)
        self.assertTrue(driver.lower_pen().ok)

    def test_disconnect_failure_is_reported(self) -> None:
        driver = Driver(bridge=FakeBridge(fail_on="disconnect"))
        driver.connect()

        result = driver.disconnect()

        self.assertFalse(result.ok)
        self.assertIn("failed disconnect", result.message)
        self.assertEqual(driver.get_progress().state, "idle")

    def test_connect_runtime_failure_is_reported(self) -> None:
        driver = Driver(bridge=FakeBridge(fail_with_runtime_on="connect"))

        result = driver.connect()

        self.assertFalse(result.ok)
        self.assertIn("runtime failed connect", result.message)
        self.assertEqual(driver.get_progress().state, "idle")

    def test_status_failure_updates_progress_message(self) -> None:
        driver = Driver(bridge=FakeBridge(fail_on="status"))
        driver.connect()

        result = driver.status()

        self.assertFalse(result.ok)
        self.assertIn("failed status", result.message)
        self.assertIn("Status failed", driver.get_progress().message)

    def test_pen_action_failure_updates_progress_message(self) -> None:
        driver = Driver(bridge=FakeBridge(fail_on="raise_pen"))
        driver.connect()

        result = driver.raise_pen()

        self.assertFalse(result.ok)
        self.assertIn("failed raise_pen", result.message)
        self.assertIn("Pen raise failed", driver.get_progress().message)

    def test_driver_uses_machine_settings_for_bridge_configuration(self) -> None:
        machine_yaml = """
name: machine-dev
machine_model: idraw-2.0
port: COM9
baudrate: 57600
serial_timeout: 2.5
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            machine_path = pathlib.Path(tmp_dir) / "machine.yaml"
            machine_path.write_text(machine_yaml.strip() + "\n", encoding="utf-8")
            machine_settings = load_machine_settings(machine_path)
            driver = Driver(machine_settings=machine_settings)

        self.assertEqual(driver.bridge.port, "COM9")
        self.assertEqual(driver.bridge.baudrate, 57600)
        self.assertEqual(driver.bridge.timeout, 2.5)

    def test_driver_uses_plot_profile_for_pen_commands(self) -> None:
        profile_yaml = """
name: dev
pen_up_command: M300 S30
pen_down_command: M300 S50
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            profile_path = pathlib.Path(tmp_dir) / "profile.yaml"
            profile_path.write_text(profile_yaml.strip() + "\n", encoding="utf-8")

            plot_profile = load_plot_profile(profile_path)
            driver = Driver(plot_profile=plot_profile)

        self.assertEqual(driver.bridge.pen_up_command, "M300 S30")
        self.assertEqual(driver.bridge.pen_down_command, "M300 S50")

    def test_driver_uses_profile_motion_parameters_for_bridge(self) -> None:
        profile_yaml = """
name: speeds-and-heights
pen_up_height: 0.8
pen_down_height: 4.2
speed_penup: 9100
speed_pendown: 1900
pen_move_speed: 7300
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            profile_path = pathlib.Path(tmp_dir) / "profile.yaml"
            profile_path.write_text(profile_yaml.strip() + "\n", encoding="utf-8")
            plot_profile = load_plot_profile(profile_path)

            driver = Driver(plot_profile=plot_profile)

        self.assertEqual(driver.bridge.pen_up_z, 0.8)
        self.assertEqual(driver.bridge.pen_down_z, 4.2)
        self.assertEqual(driver.bridge.speed_penup, 9100)
        self.assertEqual(driver.bridge.speed_pendown, 1900)
        self.assertEqual(driver.bridge.pen_move_speed, 7300)

    def test_driver_motion_parameters_fallback_to_model_defaults(self) -> None:
        driver = Driver()

        self.assertEqual(driver.bridge.pen_up_z, driver.plot_profile.pen_up_height)
        self.assertEqual(driver.bridge.pen_down_z, driver.plot_profile.pen_down_height)
        self.assertEqual(driver.bridge.speed_penup, driver.plot_profile.speed_penup)
        self.assertEqual(driver.bridge.speed_pendown, driver.plot_profile.speed_pendown)
        self.assertEqual(driver.bridge.pen_move_speed, driver.plot_profile.speed_penup)

    def test_loaders_reject_unknown_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            machine_path = pathlib.Path(tmp_dir) / "machine.yaml"
            plot_path = pathlib.Path(tmp_dir) / "profile.yaml"
            app_state_path = pathlib.Path(tmp_dir) / "app_state.yaml"

            machine_path.write_text(
                yaml.safe_dump({"machine_model": "idraw-2.0", "bad": 1}),
                encoding="utf-8",
            )
            plot_path.write_text(
                yaml.safe_dump({"name": "default", "oops": True}),
                encoding="utf-8",
            )
            app_state_path.write_text(
                yaml.safe_dump({"active_profile": "default", "extra": "x"}),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_machine_settings(machine_path)

            with self.assertRaises(ValueError):
                load_plot_profile(plot_path)

            with self.assertRaises(ValueError):
                load_app_state(app_state_path)

    def test_driver_from_config_files_wires_machine_and_profile(self) -> None:
        machine_yaml = """
name: m1
machine_model: idraw-2.0
port: COM7
baudrate: 230400
serial_timeout: 1.7
"""
        profile_yaml = """
name: p1
pen_up_height: 0.9
pen_down_height: 3.3
pen_move_speed: 7000
speed_penup: 6500
speed_pendown: 1800
pen_up_command: M5
pen_down_command: M3 S900
"""

        with tempfile.TemporaryDirectory() as tmp_dir:
            machine_path = pathlib.Path(tmp_dir) / "machine.yaml"
            profile_path = pathlib.Path(tmp_dir) / "profile.yaml"
            machine_path.write_text(machine_yaml.strip() + "\n", encoding="utf-8")
            profile_path.write_text(profile_yaml.strip() + "\n", encoding="utf-8")

            driver = Driver.from_config_files(machine_path, profile_path)

        self.assertEqual(driver.bridge.port, "COM7")
        self.assertEqual(driver.bridge.baudrate, 230400)
        self.assertEqual(driver.bridge.timeout, 1.7)
        self.assertEqual(driver.bridge.pen_up_z, 0.9)
        self.assertEqual(driver.bridge.pen_down_z, 3.3)
        self.assertEqual(driver.bridge.pen_move_speed, 7000)
        self.assertEqual(driver.bridge.speed_penup, 6500)
        self.assertEqual(driver.bridge.speed_pendown, 1800)
        self.assertEqual(driver.bridge.pen_up_command, "M5")
        self.assertEqual(driver.bridge.pen_down_command, "M3 S900")


if __name__ == "__main__":
    unittest.main()
