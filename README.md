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
$env:PYTHONPATH="src"
python -m idraw_ui.app
```

The UI is now built with `customtkinter` for a cleaner visual style and exposes
the first operational machine controls:

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

## Documentation

- Hardware observations and validated axis mapping:
	- `docs/hardware_notes.md`
- Architecture roles and implementation decisions:
	- `docs/architecture_decisions.md`

## Profile-driven backend config

The UI now uses a persistent settings layer backed by YAML files.
The active profile and profile values are saved automatically as the user changes them.

### Current profile persistence behavior

- The active profile is loaded from `settings/app_state.yaml` at startup.
- Profile values are written to YAML files under `profiles/`.
- Changing a plot option in the UI immediately updates the current profile and persists it.
- A new profile can be created from the UI through the header action.

### Files involved

- `settings/app_state.yaml` stores the active profile and small app-state values.
- `settings/machine.yaml` stores machine configuration.
- `profiles/*.yaml` stores individual plot profiles.

### Example profile keys

Supported profile keys for the current plot profile include:

- `name`
- `pen_up_height`
- `pen_down_height`
- `pen_move_speed`
- `speed_penup`
- `speed_pendown`
- `accel`
- `auto_rotate`
- `reordering`
- `preview`
- `digest`
- `pen_up_command`
- `pen_down_command`

## Development tooling

For local formatting and linting, install the development hook once in the
project environment:

```powershell
python -m pip install pre-commit
python -m pre_commit install
```

This uses Ruff to automatically format and lint Python files before each commit.
