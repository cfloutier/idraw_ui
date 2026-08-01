from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import serial
from serial.tools import list_ports


DRAWCORE_VID_PIDS = ("1A86:7523", "1A86:8040")


class VendorBridgeError(RuntimeError):
    """Raised when a hardware bridge command fails."""


@dataclass(frozen=True)
class CandidatePort:
    device: str
    description: str
    hwid: str


class VendorBridge:
    """Serial bridge for DrawCore/iDraw-compatible controllers."""

    def __init__(
        self,
        bundle_path: str | None = None,
        *,
        port: str | None = None,
        baudrate: int = 115200,
        timeout: float = 1.0,
        pen_up_command: str | None = None,
        pen_down_command: str | None = None,
        pen_up_z: float = 0.5,
        pen_down_z: float = 5.0,
        pen_move_speed: float = 8000.0,
        speed_penup: float = 8000.0,
        speed_pendown: float = 2000.0,
    ) -> None:
        self.bundle_path = bundle_path
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.pen_up_command = pen_up_command
        self.pen_down_command = pen_down_command
        self.pen_up_z = pen_up_z
        self.pen_down_z = pen_down_z
        self.pen_move_speed = pen_move_speed
        self.speed_penup = speed_penup
        self.speed_pendown = speed_pendown
        self.connected = False
        self._serial: Optional[serial.Serial] = None

    @staticmethod
    def _normalize_command(command: str) -> str:
        command = command.strip()
        if not command:
            raise VendorBridgeError("Command cannot be empty")
        if not command.endswith("\r"):
            command = f"{command}\r"
        return command

    def find_drawcore_ports(self) -> list[CandidatePort]:
        candidates: list[CandidatePort] = []
        for item in list_ports.comports():
            if any(vidpid in item.hwid for vidpid in DRAWCORE_VID_PIDS):
                candidates.append(
                    CandidatePort(item.device, item.description, item.hwid)
                )
        return candidates

    def _require_connection(self) -> serial.Serial:
        if self._serial is None or not self._serial.is_open:
            raise VendorBridgeError("Device is not connected")
        return self._serial

    def _query_line(self, command: str, retries: int = 20) -> str:
        ser = self._require_connection()
        ser.write(command.encode("ascii"))
        for _ in range(retries):
            raw = ser.readline().decode("ascii", errors="replace").strip()
            if raw:
                return raw
        return ""

    def _query_best_line(
        self,
        command: str,
        preferred_prefixes: tuple[str, ...],
        retries: int = 30,
    ) -> str:
        ser = self._require_connection()
        ser.write(command.encode("ascii"))
        lines: list[str] = []
        for _ in range(retries):
            raw = ser.readline().decode("ascii", errors="replace").strip()
            if not raw:
                continue
            lines.append(raw)
            if raw.startswith(preferred_prefixes):
                return raw
        return lines[0] if lines else ""

    def _run_command_expect_ok(self, command: str, retries: int = 100) -> str:
        ser = self._require_connection()
        ser.write(command.encode("ascii"))
        last_line = ""
        for _ in range(retries):
            last_line = ser.readline().decode("ascii", errors="replace").strip()
            if not last_line:
                continue
            if last_line.lower().startswith("ok"):
                return last_line
        if last_line:
            raise VendorBridgeError(
                f"Command {command.strip()!r} did not return ok, last response={last_line!r}"
            )
        raise VendorBridgeError(f"Command {command.strip()!r} timed out")

    def connect(self) -> bool:
        if self.connected and self._serial is not None and self._serial.is_open:
            return True

        selected_port = self.port
        if not selected_port:
            ports = self.find_drawcore_ports()
            if not ports:
                raise VendorBridgeError("No DrawCore-compatible USB device detected")
            selected_port = ports[0].device

        ser = serial.Serial(
            port=selected_port, baudrate=self.baudrate, timeout=self.timeout
        )
        ser.rts = False
        ser.dtr = False
        self._serial = ser
        self.port = selected_port

        try:
            # Boot/status preamble used by DrawCore integrations.
            self._query_line("$B\r", retries=2)
            self._query_line("$B\r", retries=2)
            ser.reset_input_buffer()

            version_response = self._query_best_line(
                "V\r", preferred_prefixes=("DrawCore",)
            )
            if not version_response:
                raise VendorBridgeError(
                    "No response received from firmware version query"
                )
        except Exception:
            ser.close()
            self._serial = None
            self.connected = False
            raise

        self.connected = True
        return self.connected

    def disconnect(self) -> None:
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
        self._serial = None
        self.connected = False

    def get_status(self) -> str:
        status = self._query_best_line("?\r", preferred_prefixes=("<",))
        if not status:
            raise VendorBridgeError("No status response received")
        return status

    def home(self) -> str:
        return self._run_command_expect_ok("$H\r")

    def _move_pen(self, z_pos: float, feed_restore: float) -> str:
        command = f"G1G90 Z{z_pos:.3f}F{self.pen_move_speed:.1f}\r"
        response = self._run_command_expect_ok(command)
        self._run_command_expect_ok(f"G1 F{feed_restore:.1f}\r")
        return response

    def raise_pen(self) -> str:
        if self.pen_up_command:
            return self._run_command_expect_ok(
                self._normalize_command(self.pen_up_command)
            )
        return self._move_pen(self.pen_up_z, self.speed_penup)

    def lower_pen(self) -> str:
        if self.pen_down_command:
            return self._run_command_expect_ok(
                self._normalize_command(self.pen_down_command)
            )
        return self._move_pen(self.pen_down_z, self.speed_pendown)

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "name": "drawcore_serial_bridge",
            "connected": self.connected,
            "bundle_path": self.bundle_path,
            "port": self.port,
            "baudrate": self.baudrate,
            "pen_up_command": self.pen_up_command,
            "pen_down_command": self.pen_down_command,
            "pen_up_z": self.pen_up_z,
            "pen_down_z": self.pen_down_z,
            "pen_move_speed": self.pen_move_speed,
            "speed_penup": self.speed_penup,
            "speed_pendown": self.speed_pendown,
        }
