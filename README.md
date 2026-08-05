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
the current operational workflow through five tabs:

- `Trace`: load or reload an SVG, start/pause/stop a plot, and access quick
	`Home`, `Center`, `Pen Up`, and `Pen Down` actions.
- `Jog`: manual homing, centering, and XY jogging.
- `Pen`: pen height tuning and live pen tests.
- `Draw Options`: speed, acceleration, ordering, and preview defaults.
- `Machine`: machine model selection.

The loaded SVG name is shown in the top bar. Operational state, timing, and
distance metrics are consolidated in the colored footer status area.

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
- The last selected SVG path is remembered so `Reload` can reopen it on demand
	after restarting the app.

### Files involved

- `settings/app_state.yaml` stores the active profile, small app-state values,
  and the last SVG path/folder used by the Trace page.
- `settings/machine.yaml` stores machine configuration.
- `profiles/*.yaml` stores individual plot profiles.

### Advanced machine settings

The main UI is intentionally centered on the machine model selection.
Some lower-level serial settings still exist in `settings/machine.yaml`, but they
are considered advanced settings and are expected to be edited manually when needed.

Current advanced keys:

- `port`
- `baudrate`
- `serial_timeout`
- `digest`

Recommended behavior:

- Leave `port: null` to keep automatic machine selection enabled.
- Only set a specific `port` when you explicitly want to force one device.
- Keep `baudrate` and `serial_timeout` at their defaults unless you are debugging
	or working around a specific hardware/firmware issue.
- Keep `digest: 1` unless you explicitly need another runtime behavior:
	- `0`: disabled
	- `1`: normal plotting with digest/plob output support (recommended)
	- `2`: digest-only processing (no plotting)

Example:

```yaml
baudrate: 115200
digest: 1
machine_model: idraw-a1
name: machine-default
port: null
serial_timeout: 1.0
```

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
- `pen_up_command`
- `pen_down_command`

### Important note: speed units and time estimation

The UI exposes speed sliders as `mm/min` values (`speed_penup`, `speed_pendown`).

During estimation (`prepare`, preview mode), these values are converted to the
runtime scale expected by the iDraw internal estimator:

- `in/s = mm/min / (25.4 * 60)`

Why this matters:

- Without this conversion, large UI speed values can produce nearly identical
	estimated times (saturation effect).
- With conversion applied in preview mode, the estimate becomes sensitive to
	speed changes again.

Safety rule implemented in code:

- Conversion is applied only for estimation/preview sessions.
- Real plotting sessions keep the raw profile speed values unchanged.

## Development tooling

For local formatting and linting, install the development hook once in the
project environment:

```powershell
python -m pip install pre-commit
python -m pre_commit install
```

This uses Ruff to automatically format and lint Python files before each commit.
