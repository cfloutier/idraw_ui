from __future__ import annotations

from typing import Any


class VendorBridge:
    """Placeholder for vendor-specific integration with the iDraw runtime bundle."""

    def __init__(self, bundle_path: str | None = None) -> None:
        self.bundle_path = bundle_path
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        return self.connected

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "name": "idraw_vendor_bridge",
            "connected": self.connected,
            "bundle_path": self.bundle_path,
        }
