# AI Handoff Plan

## Current validated status

The following points are now implemented and validated on real tests:

- Play was tested and validated.
- Status handling in UI is OK (including working states, colored feedback flow, and footer metrics).
- Manual actions added and validated:
  - Home
  - Center
  - Pen Up
  - Pen Down
  - Jog controls
- Persistent profile management is now implemented.
- Profile changes are saved immediately as the user edits them.
- Creating a new profile from the UI is now supported.
- Machine advanced setting `digest` is persisted in `settings/machine.yaml`.

Additional behavior now in place:

- Manual actions run with auto connect -> action -> auto disconnect.
- Plot runtime can take control without requiring manual disconnect first.
- Manual action stop is handled as best effort via disconnect.
- The active profile is persisted through `settings/app_state.yaml`.
- Profile files are stored under `profiles/` and reloaded on startup.
- The last SVG path is remembered so `Reload` can reuse it after restarting the app.
- Startup does not auto-load the last SVG; it only enables `Reload` when a valid path is known.
- The top bar only shows the currently loaded SVG name.
- Operational state and plot metrics are consolidated in the colored footer status area.
- The Trace tab now includes quick actions for `Home`, `Center`, `Pen Up`, and `Pen Down`.
- Speed estimation now uses preview-only unit conversion from UI `mm/min` values to runtime `in/s` values.
- Real plotting keeps the raw profile speed values unchanged; the conversion affects estimation only.
- Estimate diagnostics now log both the UI speed values and the converted preview values.

Current UI shape:

- `Trace`: `Load SVG`, `Reload`, `Play/Pause/Stop`, quick `Home/Center/Pen Up/Pen Down`, and log view.
- `Jog`: homing, centering, XY jog controls, and jog-distance persistence.
- `Pen`: pen height tuning, live apply toggle, reset, and pen test actions.
- `Draw Options`: speed/acceleration and plot options merged into one page.
- `Machine`: machine model selection.

## Architecture choices kept for continuity

- UI entrypoint for operations: AppWindow.
- Application backend API boundary: Driver.
- Direct machine serial commands: VendorBridge.
- Plot runtime boundary: Idraw2Facade.
- Concrete internal runtime adapter: Idraw2InternalRuntime.

This separation must stay in place to avoid coupling UI directly to runtime internals.

## Next plans (from current project direction)

1. Machine configuration refinements:

- decide whether additional advanced machine settings should stay file-only or get selective UI exposure
- document the intended operator workflow for `digest` and reload/estimate behavior

2. Table calibration management:

- table size setup
- preferred home selection
- calibration page should be able to draw placement frames for common paper sizes:
  - A4
  - A3
  - A2
  - Letter
  - Raisin

3. SVG rotation handling:

- choosing the home position will imply different SVG orientations
- rotate SVG automatically according to chosen home/calibration orientation

4. Home and center semantics:

- redefine `Home` behavior according to the selected machine size
- redefine `Center` behavior according to the selected machine size
- keep these commands aligned with the chosen home corner/orientation rules

5. Movement speed tuning:

- decide whether UI labels or docs should explicitly surface the `mm/min` -> `in/s` estimation conversion
- validate estimation sensitivity on a wider set of large SVGs
²
## Practical note for next contributors

- Keep validating each change on real hardware before locking conventions.
- Keep hardware observations synchronized with docs/hardware_notes.md.
- Keep architecture and decision rationale synchronized with docs/architecture_decisions.md.
