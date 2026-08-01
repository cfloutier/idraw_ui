# idraw_ui

Prototype UI and application layer for the new iDraw-based workflow.

This repository is intentionally started as a clean slate, with a clear separation between:

- UI layer
- application/backend layer
- vendor bridge to the iDraw runtime bundle

## Architecture goal

- The UI should talk to a stable application API, not directly to the vendor internals.
- Profiles and machine settings are owned by the application layer.
- Vendor-specific implementation details stay behind the bridge.
