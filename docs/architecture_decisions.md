# Architecture and Decisions

This document tracks the important implementation choices made for the MVP and explains the role of each core class.

## Goals

- Keep the UI independent from vendor internals.
- Keep machine settings separate from plot profile settings.
- Allow manual machine control and plot runtime control to coexist safely.
- Make runtime operations observable in UI (state, status, timings).

## Main class responsibilities

### AppWindow (UI orchestration)

File: `src/idraw_ui/ui/app_window.py`

- Owns all UI controls and state variables.
- Calls the backend through `Driver` only.
- Runs long operations in worker threads to avoid UI freeze:
  - SVG load + estimate
  - manual movement actions (home, center, jog)
- Updates state/status colors:
  - success: green
  - error: red
  - working (loading/estimating/moving): yellow
- Implements button locking rules during active operations.

### Driver (application API)

File: `src/idraw_ui/backend/driver.py`

- Single application-facing API used by UI.
- Coordinates two control paths:
  - manual serial bridge (`VendorBridge`) for direct machine commands
  - plot pipeline (`Idraw2Facade`) for load/prepare/start/pause/resume/stop
- Exposes operation results with `DriverCommandResult`.
- Synchronizes progress from plot runtime into `PlotProgress`.

### VendorBridge (direct serial control)

File: `src/idraw_ui/backend/vendor_bridge.py`

- Encapsulates direct serial communication with DrawCore-compatible firmware.
- Provides manual commands: connect/disconnect/status/home/pen up/pen down/relative move.
- Converts serial errors into `VendorBridgeError`.

### Idraw2Facade (stable plotting contract)

File: `src/idraw_ui/backend/idraw2_facade.py`

- Stable adapter boundary between app and concrete runtime implementation.
- Manages high-level plotting flow and progress state.
- Keeps runtime swappable via protocol.

### Idraw2InternalRuntime (concrete runtime adapter)

File: `src/idraw_ui/backend/idraw2_runtime.py`

- Integrates `idraw2_0internal`.
- Applies runtime options from machine/profile config.
- Computes estimate metrics and executes plotting in worker thread.
- Includes compatibility bridge for legacy `OptionParser` expectations.

### Shared models

File: `src/idraw_ui/backend/models.py`

- `MachineSettings`: machine/serial configuration.
- `PlotProfile`: plotting behavior profile.
- `PlotProgress`: runtime progress snapshot consumed by UI.
- `PlotState`: state enum used end-to-end.

## Key design decisions

### 1) Settings split: machine vs profile

Reason:
- Machine identity/port/baud are hardware concerns.
- Pen/speed/ordering/digest are plotting concerns.

Result:
- Fewer accidental regressions when changing one concern.
- Clearer configuration ownership.

### 2) UI must never call vendor internals directly

Reason:
- Keep UI maintainable and testable.
- Allow runtime replacement without UI rewrite.

Result:
- All UI actions pass through `Driver`.
- Runtime details are isolated in façade/runtime layers.

### 3) Prevent serial ownership conflicts

Reason:
- Manual bridge and plotting runtime cannot own the same serial session simultaneously.

Result:
- Before plot runtime commands, driver releases bridge if connected.
- Manual commands run as auto-connect -> action -> auto-disconnect.

### 4) Manual actions are asynchronous in UI

Reason:
- Home/Center/Jog can take noticeable time.
- UI must stay responsive.

Result:
- Manual operations run in worker threads.
- UI shows `moving` state with elapsed time.
- Manual movement buttons are locked while an action is active.

### 5) Stop behavior during manual actions is best effort

Reason:
- Some firmware commands are not truly cancellable mid-frame.

Result:
- `Stop` remains clickable during manual movement.
- Stop triggers forced disconnect (`stop_manual_action`) to interrupt as early as possible.
- This is best effort by serial teardown; exact interruption timing depends on firmware state.

### 6) Estimation uses preview-only speed scale conversion

Reason:
- UI profile speeds are represented in `mm/min`.
- The internal iDraw estimator is more coherent when speeds are provided on its
  expected scale (`in/s`) during preview.
- Empirical tests showed that skipping conversion can flatten estimates across
  very different speed values.

Result:
- For estimation (`prepare`, preview mode), speeds are converted with:
  - `in/s = mm/min / (25.4 * 60)`
- For real plotting (`start`/`resume`/`home`, non-preview), raw profile speed
  values are preserved.
- UI trace logs now print both the UI speed values and preview-converted values
  used for estimation diagnostics.

### 7) Physical home vs logical home must stay explicit

Reason:
- The legacy Inkscape extension distinguishes between the firmware homing point
  and a separate `machine_origin` helper.
- In the extension, true homing remains a DrawCore `$H` operation.
- The extension's `machine_origin` command is a special hard-coded follow-up move
  after physical homing; it is not a general user-selectable alternative corner system.
- The extension's portrait/landscape handling is focused on document rotation,
  not on redefining the meaning of home.

Result:
- In this app, `physical home` should mean the real microswitch-based homing point.
- Model metadata should describe `physical home` directly, plus whether each
  physical axis points toward home or away from it.
- Any future user-selected corner should be treated as a separate `logical home`
  or target corner, derived from the physical home by an additional motion rule.
- `Home`, `Center`, and SVG orientation rules should be built from that explicit
  distinction instead of overloading the firmware home concept.

Convention note:
- We do not use a separate `physical orientation` concept in machine model data.
- The chosen convention is that model data records the `physical_home` corner in
  the vertical table representation, then records axis polarity independently:
  - `X` can point toward home or away from home
  - `Y` can point toward home or away from home
- For the currently validated machine family, `Y` points toward home and `X`
  points away from home.

Developer note:
- The Inkscape extension is useful as a reference for serial commands and resume
  behavior, but it does not already implement the configurable four-corner home
  model planned here.

### 8) Logical home names follow our visual table convention

Reason:
- Legacy runtime terminology can describe origins using axis or document
  conventions that do not match the operator's visual understanding of the table.
- The UI needs one predictable rule for choosing a home and placing a drawing
  without leaving the usable machine area.

Result:
- The selected logical home name always identifies the visual corner of the
  table used as the drawing anchor.
- The SVG must extend inward from that corner:
  - `top-left`: right and down
  - `top-right`: left and down
  - `bottom-left`: right and up
  - `bottom-right`: left and up
- Physical-axis signs and legacy runtime names must be converted to this
  convention at the plotting boundary; they must not redefine the UI meaning.
- Bounds validation and SVG transformation must use this same convention before
  a real plot starts.

Implementation note:
- No changes are made to `idraw2_0internal` or `drawcore_plotink`.
- iDraw still extracts the digest, applies its optional page rotation, and clips
  it to positive page/machine bounds.
- The app runtime adapter applies one shared baseline orientation to the digest,
  then selects only the logical start coordinate:
  - `bottom-right`: `(0, page height)`
  - `bottom-left`: `(0, 0)`
  - `top-right`: `(page width, page height)`
  - `top-left`: `(page width, 0)`
- Logical-home selection must not mirror the digest. The selected start corner
  already makes all positive page coordinates extend inward; an additional
  home-specific mirror changes the content orientation.
- The transformed digest is stored in the PLOB resume snapshot with an app
  metadata marker. Reprocessing the same snapshot is idempotent.
- A fresh Play starts from the original SVG. PLOB snapshots are reserved for
  Resume; plotting a prepared PLOB again in `plot` mode makes the vendor runtime
  rotate its geometry a second time.
- Changing machine/profile settings invalidates the prepared snapshot and
  forces a new preparation before Play.
- Physical tests also established that SVG content was already rotated by 180
  degrees before the logical-home work. This is a separate baseline orientation
  issue, not a consequence of corner mirroring.
- The runtime adapter corrects that baseline with one global 180-degree digest
  rotation inside the positive page bounds. A versioned PLOB metadata marker
  (`idraw_ui_content_orientation=upright-v1`) prevents double rotation on Play
  or Resume. Logical-home start coordinates remain unchanged.

## SVG orientation pipeline (quick reference)

Implementation detail supporting decision 8 above.

### Portrait

- `auto_rotate = True` (vendor rotates SVG internally).
- Global X+Y mirror correction applied to digest before home placement.
- `start_pos` formula: `mirror_x = "top" in corner`, `mirror_y = "right" in corner`.

### Landscape

- `auto_rotate = False` (vendor rotation conflicts with our correction).
- Global X+Y mirror skipped (raw digest arrives already upright).
- `start_pos` formula: `(mirror_x, mirror_y) = (portrait_mirror_y, NOT portrait_mirror_x)`.

Metadata key `idraw_ui_content_orientation` in the PLOB prevents double correction
on Resume.

## Adding and validating a machine model

Machine definitions live in `src/idraw_ui/backend/machine_models.py` inside
`_MODEL_DEFINITIONS`. Do not silently reuse a model merely because its page size
is similar: travel size, firmware model ID, physical home, axis assignment, and
axis polarity must all match.

### Field reference

| Field | Description |
| --- | --- |
| `key` | Unique string identifier |
| `label` | Display name in the UI |
| `runtime_model` | Vendor firmware model ID |
| `width_mm` / `height_mm` | Usable travel in the machine's native landscape convention |
| `physical_home` | Visual corner reached by firmware homing **in portrait orientation** |
| `my_home_corner` | Safest default logical home for this model |
| `long_axis_is_y` | True if firmware Y drives the long table axis |
| `x_axis_toward_home` | True if positive X command moves toward the physical home |
| `y_axis_toward_home` | True if positive Y command moves toward the physical home |

Example:

```python
MachineModelDefinition(
    key="idraw-my-model",
    label="iDraw My Model",
    runtime_model=0,  # replace with verified vendor model ID
    width_mm=500,
    height_mm=350,
    physical_home="bottom-right",
    my_home_corner="top-left",
    long_axis_is_y=True,
    x_axis_toward_home=False,
    y_axis_toward_home=True,
),
```

### Validation protocol

1. Remove the pen and keep the carriage near the centre.
2. Use very short physical jogs to identify `+X`, `-X`, `+Y`, `-Y` directions.
3. Verify `Physical Home`.
4. Verify `Center` only after home and jog directions are correct.
5. Run the full A6 safety test for portrait orientation and all homes to be supported.
6. Validate landscape independently.
7. Run the unit tests:

```powershell
python -m pytest tests\test_machine_models.py tests\test_machine_tab.py
```

Record the physical result in `docs/hardware_notes.md`. A model should only be
offered as validated after home, jog directions, centre move, A6 placement,
upright orientation, and bounds preview have all passed on real hardware.

If the model cannot yet be added, record at least: exact product name, firmware
version, vendor runtime model ID, usable travel dimensions, portrait physical-home
corner, which firmware axis drives the long side, and the observed `+X`/`+Y` jog
directions from centre.

## Operational notes

- Axis mapping and hardware validation logs are tracked in `docs/hardware_notes.md`.
- Use short jog moves to validate direction assumptions before large offsets.
- Keep `Center` semantics aligned with validated axis mapping.

## Future improvements

- Add explicit command queue/cancellation tokens for manual actions.
- Add integration tests for serial ownership transitions.
- Add configurable center offsets in profile or machine settings.
- Add UI hint when `Stop` interruption is pending.
