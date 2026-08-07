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
- Inkscape extension analysis confirmed that legacy `home` remains the physical
  firmware homing point, while `machine_origin` is only a special hard-coded
  post-home move, not a full alternative-corner system.
- Machine model metadata now stores `physical_home` and per-axis polarity
  (`toward home` vs `inverse`) instead of a separate `physical_orientation` concept.
- Machine model metadata now also stores axis-layout conventions
  (`long_axis_is_y`, `x_axis_toward_home`, `y_axis_toward_home`) used as the
  geometry source of truth.
- Logical home support is implemented with:
  - `my_home_corner`
  - `my_home_padding_mm`
  - `go_to_my_home()` movement built from machine geometry
- Centering for test moves now uses machine geometry
  (`move_delta_to_center`) instead of fixed deltas.
- Machine tab now renders and controls:
  - table orientation
  - selected logical home corner
  - configurable safety padding in mm
  - preview markers for physical home, logical home, and padded inset area
  - explanatory copy: orientation means physical placement on table and affects jog
- Jog tab now has two operational modes:
  - physical axis mode (`+X/-X/+Y/-Y`)
  - table-relative mode (`right/left/forward/backward`)
- Jog mode is persisted in app state (`settings/app_state.yaml`) and restored
  on startup.
- Table-relative jog mapping was rewritten to a deterministic, projection-based
  geometry rule to remove apparent random X inversions.

Current UI shape:

- `Trace`: `Load SVG`, `Reload`, `Play/Pause/Stop`, quick `Home/Center/Pen Up/Pen Down`, and log view.
- `Jog`: homing, centering, dual jog modes, jog-distance persistence, and
  persisted jog mode selection.
- `Pen`: pen height tuning, live apply toggle, reset, and pen test actions.
- `Draw Options`: speed/acceleration and plot options merged into one page.
- `Machine`: machine model, table orientation, logical home corner, home padding,
  and geometry preview.

## Architecture choices kept for continuity

- UI entrypoint for operations: AppWindow.
- Application backend API boundary: Driver.
- Direct machine serial commands: VendorBridge.
- Plot runtime boundary: Idraw2Facade.
- Concrete internal runtime adapter: Idraw2InternalRuntime.

This separation must stay in place to avoid coupling UI directly to runtime internals.

## Next plans (from current project direction)

1. Tracing orientation adaptation

- During trace execution, adapt orientation so the drawing is placed correctly
  for the selected table/machine conventions.

2. Post-load SVG preview mode

- After loading an SVG, show a preview of the SVG footprint/gabarit as read from
  the file against the table and current Machine tab choices.

3. SVG transformation pipeline

- Orient the SVG correctly from those machine choices, potentially by
  transforming/manipulating the SVG on the fly.

4. README split pass (before new tool proposal)

- Before proposing the position-mark tool, do a full README pass to separate
  developer-facing notes from user-facing documentation.

5. Position-mark drawing tool

- Add a tool to draw paper/page placement marks on the table.

6. Time-estimation refinement

- Improve and calibrate time-estimation calculations.

7. Play/Pause reliability fixes

- Investigate and fix remaining Play/Pause edge cases.
- Specific priority: dot-heavy jobs where points are currently lost.

## Practical note for next contributors

- Keep validating each change on real hardware before locking conventions.
- Keep hardware observations synchronized with docs/hardware_notes.md.
- Keep architecture and decision rationale synchronized with docs/architecture_decisions.md.
