from __future__ import annotations

import unittest
from unittest.mock import patch

import serial

from idraw_ui.backend.vendor_bridge import VendorBridge, VendorBridgeError


class FakeSerial:
    def __init__(self, *, lines: list[bytes] | None = None) -> None:
        self._lines = lines or []
        self.is_open = True
        self.rts = False
        self.dtr = False

    def write(self, _data: bytes) -> int:
        return 1

    def readline(self) -> bytes:
        if self._lines:
            return self._lines.pop(0)
        return b""

    def reset_input_buffer(self) -> None:
        return

    def close(self) -> None:
        self.is_open = False


class VendorBridgeRobustnessTests(unittest.TestCase):
    def test_connect_wraps_serial_open_error(self) -> None:
        bridge = VendorBridge(port="COM42")

        with patch("idraw_ui.backend.vendor_bridge.serial.Serial") as serial_ctor:
            serial_ctor.side_effect = serial.SerialException("port busy")

            with self.assertRaises(VendorBridgeError) as ctx:
                bridge.connect()

        self.assertIn("Failed to open serial port", str(ctx.exception))
        self.assertIn("COM42", str(ctx.exception))

    def test_get_status_wraps_serial_io_error(self) -> None:
        bridge = VendorBridge(port="COM5")
        bridge._serial = FakeSerial()  # test fixture for connected state

        with (
            patch.object(
                bridge._serial, "write", side_effect=serial.SerialException("usb gone")
            ),
            self.assertRaises(VendorBridgeError) as ctx,
        ):
            bridge.get_status()

        self.assertIn("Serial communication error", str(ctx.exception))

    def test_home_wraps_serial_io_error(self) -> None:
        bridge = VendorBridge(port="COM5")
        bridge._serial = FakeSerial()

        with (
            patch.object(
                bridge._serial,
                "write",
                side_effect=serial.SerialException("write failed"),
            ),
            self.assertRaises(VendorBridgeError) as ctx,
        ):
            bridge.home()

        self.assertIn("Serial communication error", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
