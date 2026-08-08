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
the current operational workflow through six tabs:

- `Trace`: load or reload an SVG, start/pause/stop a plot, and access quick
	`My home`, `Center`, `Pen Up`, and `Pen Down` actions. Its table preview shows
	the loaded SVG placement, selected home, orientation, dimensions, and bounds.
- `Jog`: manual homing, centering, and XY jogging.
- `Pen`: pen height tuning and live pen tests.
- `Draw Options`: speed, acceleration, ordering, and preview defaults.
- `Machine`: machine model selection.
- `Log`: diagnostic output intended for development and troubleshooting.

The loaded SVG name is shown in the top bar. Operational state, timing, and
distance metrics are consolidated in the colored footer status area.

## Mandatory safety test before first use

Run this procedure before using the application with a machine that has not yet
been validated. Repeat it after adding or changing a machine model, its table
orientation, or its axis configuration.

This qualification reduces the risk of an incorrect move; it cannot guarantee
mechanical safety. Keep the machine supervised and remain ready to stop it during
every validation run.

Every application `Home`, `My home`, and `Center` action sends `Pen Up` before
starting the homing move. If raising the pen fails, the movement is aborted. Do
not bypass that failure: raise the pen manually with the machine stopped, then
diagnose the pen command before trying again.

### Prepare the test

1. Clear the whole plotter area and keep access to the emergency stop or power
	switch.
2. Remove the pen for the first dry run, or make certain that it stays fully
	raised.
3. In `Machine`, select the exact physical plotter model.
4. Select the physical table orientation and the desired `My home` corner.
5. With the motors disabled or the machine powered off, move the carriage by
	hand near the center of the usable area. Do not force a powered motor.
6. Power or enable the machine again without asking the application to perform
	a long positioning move.
7. In `Trace`, load `test_svg_files/_test_a6.svg`.
8. Check the preview before pressing `Play`:
	- the orange home marker must match the selected corner;
	- the A6 page must appear in the expected area of the table;
	- `OUT OF BOUNDS` must not be displayed.

### Validate the selected home

Start the test with the carriage near the center so there is at least one A6
page of free travel in every direction. Be ready to press `Stop` or cut power as
soon as the first move heads the wrong way.

The drawing must extend inward from the selected visual home:

| Selected `My home` | Expected drawing direction from the center |
| --- | --- |
| `top-left` | right and down |
| `top-right` | left and down |
| `bottom-left` | right and up |
| `bottom-right` | left and up |

1. Press `Play` for the dry run and verify the first moves against this table.
2. Stop immediately if either direction is wrong or if the carriage approaches
	a mechanical limit.
3. If the dry run is correct, install the pen and repeat the A6 test on paper.
4. Confirm that the page is drawn in the expected zone, the `Up` arrow points
	toward the visual top of the table, and `A6 Test` is upright and not mirrored.
5. Repeat the procedure for every home corner that will actually be used.

Do not use the application for production plotting if this test fails. A wrong
direction means that the selected model does not describe the physical machine,
or that the real model is missing from the application.

## Adding and validating a machine model

Machine definitions live in
`src/idraw_ui/backend/machine_models.py` inside `_MODEL_DEFINITIONS`. Do not
silently reuse a model merely because its page size is similar: travel size,
firmware model ID, physical home, axis assignment, and axis polarity must all
match.

### Add the definition

1. Copy the closest existing `MachineModelDefinition` entry and give it a unique
	`key` and user-facing `label`.
2. Set `runtime_model` to the model ID expected by the vendor iDraw runtime.
	Verify this value from the machine/vendor documentation; do not guess it.
3. Set `width_mm` and `height_mm` to the usable travel dimensions in the
	machine's native landscape convention. The UI swaps them for portrait display.
4. Set `physical_home` to the visual corner reached by firmware homing in
	portrait orientation: `top-left`, `top-right`, `bottom-left`, or
	`bottom-right`.
5. Set `my_home_corner` to the safest default logical home for this model.
6. Set `long_axis_is_y` according to whether firmware Y drives the long table
	axis.
7. Set `x_axis_toward_home` and `y_axis_toward_home` according to whether the
	positive firmware direction for each axis moves toward the physical home.
8. Add legacy or alternative names to `_MODEL_ALIASES` only when they refer to
	exactly the same physical model.
9. Restart the application, select the new model in `Machine`, and verify that
	the displayed table dimensions and physical-home marker match the hardware.

Example structure:

```python
MachineModelDefinition(
	 key="idraw-my-model",
	 label="iDraw My Model",
	 runtime_model=0,  # Replace with the verified vendor model ID.
	 width_mm=500,
	 height_mm=350,
	 physical_home="bottom-right",
	 my_home_corner="top-left",
	 long_axis_is_y=True,
	 x_axis_toward_home=False,
	 y_axis_toward_home=True,
),
```

### Calibrate and validate the definition

1. Remove the pen and keep the carriage near the center.
2. Use very short physical jogs to identify actual `+X`, `-X`, `+Y`, and `-Y`
	directions. Correct the axis metadata if the UI preview and motion disagree.
3. Verify `Physical Home` with enough clear travel and immediate access to the
	stop or power control.
4. Verify `Center` only after the physical home and jog directions are correct.
5. Run the full A6 safety test above for portrait orientation and all homes that
	will be supported.
6. Validate landscape independently; do not infer it solely from portrait.
7. Add or update tests in `tests/test_machine_models.py`, then run:

```powershell
python -m unittest tests.test_machine_models tests.test_machine_tab
```

Record the physical result in `docs/hardware_notes.md`. A model should only be
offered as validated after its home, jog directions, center move, A6 placement,
upright orientation, and bounds preview have all passed on real hardware.

If the model cannot yet be added, report it as unsupported rather than selecting
an approximate model. Record at least the exact product name, firmware version,
vendor runtime model ID, usable travel dimensions, portrait physical-home
corner, which firmware axis drives the long side, and the observed directions
of short `+X` and `+Y` jogs from the center. These facts are required to create a
definition that can be validated safely.

## Recent progress (Aug 2026)

The following behavior is now implemented in the MVP UI and backend:

- Machine model metadata now defines explicit axis conventions
	(`long_axis_is_y`, `x_axis_toward_home`, `y_axis_toward_home`).
- `Home` semantics are split clearly:
	- `Physical Home`: firmware/microswitch home.
	- `My home`: selected corner plus four configurable drawing margins.
- `Center` now computes a real machine center move from machine geometry
	and table orientation.
- Machine tab now includes:
	- `My home` corner selector.
	- Integer top, bottom, left, and right drawing margins (mm).
	- Preview rendering for physical home, selected home, and the usable inset area.
	- Orientation helper text clarifying this is the physical placement of the
		plotter on the table and that it affects jog directions.
- Jog tab now includes two modes:
	- `physical`: `+X/-X/+Y/-Y`
	- `table`: `right/left/forward/backward`
- Jog mode is persisted in `settings/app_state.yaml` (app-level state,
	independent from drawing profiles).
- Table-relative jog direction mapping is deterministic and geometry-based
	(no heuristic axis flip).

## Next milestones

Planned work, in current priority order:

1. Adapt tracing orientation so drawings are placed correctly relative to the
	 selected machine/table setup.
2. Add a post-load SVG preview mode showing the SVG footprint/gabarit against
	 the table and current Machine tab choices.
3. Apply correct SVG orientation automatically, potentially by transforming the
	 SVG on the fly.
4. Before proposing the positioning-mark tool, run a full README pass to split
	 developer-oriented notes from user-facing documentation.
5. Add a positioning-mark tool to draw page placement marks on the table.
6. Refine time-estimation calculations.
7. Investigate and fix remaining Play/Pause edge cases, especially missing
	 points in dot-heavy drawings.

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
drawing_margin_bottom_mm: 10
drawing_margin_left_mm: 10
drawing_margin_right_mm: 10
drawing_margin_top_mm: 10
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
