from __future__ import annotations

import pathlib
import sys
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from idraw_ui.backend.driver import Driver  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
