from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from idraw_ui.backend.driver import Driver  # noqa: E402
from idraw_ui.backend.profiles import load_machine_profile  # noqa: E402
from idraw_ui.backend.vendor_bridge import VendorBridgeError  # noqa: E402


class FakeBridge:
    def __init__(self, *, fail_on: str | None = None) -> None:
        self.fail_on = fail_on
        self.connected = False

    def _maybe_fail(self, op: str) -> None:
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

    def test_driver_uses_profile_field_for_bridge_configuration(self) -> None:
        profile_yaml = """
name: dev
machine_model: idraw-2.0
port: COM9
baudrate: 57600
serial_timeout: 2.5
pen_up_command: M300 S30
pen_down_command: M300 S50
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            profile_path = pathlib.Path(tmp_dir) / "profile.yaml"
            profile_path.write_text(profile_yaml.strip() + "\n", encoding="utf-8")

            driver = Driver.from_profile_file(profile_path)

        self.assertEqual(driver.bridge.port, "COM9")
        self.assertEqual(driver.bridge.baudrate, 57600)
        self.assertEqual(driver.bridge.timeout, 2.5)
        self.assertEqual(driver.bridge.pen_up_command, "M300 S30")
        self.assertEqual(driver.bridge.pen_down_command, "M300 S50")

    def test_profile_loader_keeps_extra_fields(self) -> None:
        profile_yaml = """
name: profile-extra
machine_model: idraw-2.0
custom_option: value
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            profile_path = pathlib.Path(tmp_dir) / "profile.yaml"
            profile_path.write_text(profile_yaml.strip() + "\n", encoding="utf-8")
            profile = load_machine_profile(profile_path)

        self.assertEqual(profile.name, "profile-extra")
        self.assertEqual(profile.machine_model, "idraw-2.0")
        self.assertEqual(profile.field["custom_option"], "value")


if __name__ == "__main__":
    unittest.main()
