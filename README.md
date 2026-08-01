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

## Environment setup (conventional)

This project uses a local virtualenv (`.venv`) and standard pip dependencies.
The single dependency entrypoint is `requirements.txt`.
`pyproject.toml` does not duplicate runtime dependencies to avoid drift.

1. Create and activate local env:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

1. Install local Python deps:

```powershell
python -m pip install -r requirements.txt
```

1. Run first hardware test:

```powershell
python scripts\test_tracer_connection.py
```

The test script now talks to DrawCore directly through `pyserial` and does not use
any import or path from the Inkscape extension folder.

## Run the MVP UI

Launch the current MVP UI from the project root:

```powershell
python -m idraw_ui.app
```

The window exposes the first operational machine controls:

- Connect
- Status
- Home
- Pen Up
- Pen Down
- Disconnect

## DrawCore dependency

`drawcore_plotink` is installed from the public GitHub repository through
`requirements.txt`, which removes any runtime dependency on
`AppData/Roaming/inkscape/extensions`.

## Profile-driven backend config

Backend runtime settings can be loaded from a YAML profile file (for example
`profiles/default.yaml`) through `Driver.from_profile_file(...)`.

Supported optional profile keys for serial behavior:

- `port` (example: `COM5`)
- `baudrate` (default: `115200`)
- `serial_timeout` (default: `1.0`)
- `pen_up_command` (default: `M5`)
- `pen_down_command` (default: `M3 S1000`)

Example:

```python
from idraw_ui.backend.driver import Driver

driver = Driver.from_profile_file("profiles/default.yaml")
result = driver.connect()
print(result.ok, result.message)
```

## Development tooling

For local formatting and linting, install the development hook once in the
project environment:

```powershell
python -m pip install pre-commit
python -m pre_commit install
```

This uses Ruff to automatically format and lint Python files before each commit.
