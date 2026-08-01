from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = Path(r"C:\Users\cflou\AppData\Roaming\inkscape\extensions\idraw_deps")
if str(VENDOR_ROOT) not in sys.path:
    sys.path.insert(0, str(VENDOR_ROOT))

from drawcore_plotink import drawcore_motion, drawcore_serial


def main() -> int:
    print("Scanning for DrawCore-compatible ports...")
    ports = drawcore_serial.listDRAWCOREports() or []
    if not ports:
        print("No DrawCore-compatible USB device detected.")
        return 1

    print(f"Found {len(ports)} port(s):")
    for port in ports:
        print(f" - {port[0]} :: {port[1]} :: {port[2]}")

    port = drawcore_serial.openPort()
    if port is None:
        print("Unable to open a DrawCore port.")
        return 2

    print(f"Opened port: {port.port}")

    version_response = drawcore_serial.queryVersion(port)
    print(f"Version handshake: {version_response!r}")

    status_response = drawcore_serial.query(port, "?\r")
    print(f"Status handshake: {status_response!r}")

    print("Sending HOME command...")
    drawcore_motion.GoHome(port)
    time.sleep(1.5)

    print("Querying status again...")
    final_status = drawcore_serial.query(port, "?\r")
    print(f"Status after HOME: {final_status!r}")

    drawcore_serial.closePort(port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
