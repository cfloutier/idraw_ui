from __future__ import annotations

import time
from dataclasses import dataclass

import serial
from serial.tools import list_ports


DRAWCORE_VID_PIDS = ("1A86:7523", "1A86:8040")


@dataclass(frozen=True)
class CandidatePort:
    device: str
    description: str
    hwid: str


def find_drawcore_ports() -> list[CandidatePort]:
    candidates: list[CandidatePort] = []
    for port in list_ports.comports():
        if any(vidpid in port.hwid for vidpid in DRAWCORE_VID_PIDS):
            candidates.append(CandidatePort(port.device, port.description, port.hwid))
    return candidates


def query_line(port: serial.Serial, command: str, retries: int = 20) -> str:
    port.write(command.encode("ascii"))
    for _ in range(retries):
        raw = port.readline().decode("ascii", errors="replace").strip()
        if raw:
            return raw
    return ""


def query_best_line(
    port: serial.Serial,
    command: str,
    preferred_prefixes: tuple[str, ...],
    retries: int = 30,
) -> str:
    port.write(command.encode("ascii"))
    lines: list[str] = []
    for _ in range(retries):
        raw = port.readline().decode("ascii", errors="replace").strip()
        if not raw:
            continue
        lines.append(raw)
        if raw.startswith(preferred_prefixes):
            return raw
    return lines[0] if lines else ""


def run_command_expect_ok(port: serial.Serial, command: str, retries: int = 100) -> str:
    port.write(command.encode("ascii"))
    last_line = ""
    for _ in range(retries):
        last_line = port.readline().decode("ascii", errors="replace").strip()
        if not last_line:
            continue
        if last_line.lower().startswith("ok"):
            return last_line
    return last_line


def main() -> int:
    print("Scanning for DrawCore-compatible ports...")
    ports = find_drawcore_ports()
    if not ports:
        print("No DrawCore-compatible USB device detected.")
        return 1

    print(f"Found {len(ports)} port(s):")
    for port in ports:
        print(f" - {port.device} :: {port.description} :: {port.hwid}")

    primary = ports[0]
    print(f"Opening port: {primary.device}")
    ser = serial.Serial(port=primary.device, baudrate=115200, timeout=1)
    ser.rts = False
    ser.dtr = False

    try:
        # Boot/status preamble used by DrawCore integrations.
        query_line(ser, "$B\r", retries=2)
        query_line(ser, "$B\r", retries=2)
        ser.reset_input_buffer()

        version_response = query_best_line(ser, "V\r", preferred_prefixes=("DrawCore",))
        print(f"Version handshake: {version_response!r}")

        status_response = query_best_line(ser, "?\r", preferred_prefixes=("<",))
        print(f"Status handshake: {status_response!r}")

        print("Sending HOME command...")
        home_reply = run_command_expect_ok(ser, "$H\r")
        if home_reply:
            print(f"HOME response: {home_reply!r}")
        time.sleep(1.5)

        print("Querying status again...")
        final_status = query_best_line(ser, "?\r", preferred_prefixes=("<",))
        print(f"Status after HOME: {final_status!r}")
    finally:
        ser.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
