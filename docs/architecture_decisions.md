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

## Operational notes

- Axis mapping and hardware validation logs are tracked in `docs/hardware_notes.md`.
- Use short jog moves to validate direction assumptions before large offsets.
- Keep `Center` semantics aligned with validated axis mapping.

## Future improvements

- Add explicit command queue/cancellation tokens for manual actions.
- Add integration tests for serial ownership transitions.
- Add configurable center offsets in profile or machine settings.
- Add UI hint when `Stop` interruption is pending.
