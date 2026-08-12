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
- Bounds are enforced. A simple warning with the red line in the ui
- Landscape and portrait mapping is validated for the idraw H A1.
- Position-mark drawing tool is implemented (`Marks` tab) to draw paper/page
  placement marks on the table.

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
  - `drawing_margin_top_mm`, `drawing_margin_bottom_mm`
  - `drawing_margin_left_mm`, `drawing_margin_right_mm`
  - `go_to_my_home()` movement built from machine geometry
- Centering for test moves now uses machine geometry
  (`move_delta_to_center`) instead of fixed deltas.
- Machine tab now renders and controls:
  - table orientation
  - selected logical home corner
  - four integer drawing margins in mm
  - preview markers for physical home, logical home, and usable inset area
  - explanatory copy: orientation means physical placement on table and affects jog
- Jog tab now has two operational modes:
  - physical axis mode (`+X/-X/+Y/-Y`)
  - table-relative mode (`right/left/forward/backward`)
- Jog mode is persisted in app state (`settings/app_state.yaml`) and restored
  on startup.
- Table-relative jog mapping was rewritten to a deterministic, projection-based
  geometry rule to remove apparent random X inversions.
- Jog tab: live position display and Set Margin buttons for margin setup from hardware.
- All Home/Center actions raise pen before homing; `_move_and_wait()` delays UI
  status until machine physically settles.
- `auto_rotate` and `preview` removed from profiles (handled internally).
- The app now owns its logical-home naming convention independently of legacy
  runtime terminology. The home name is the visual table corner used as anchor,
  and the drawing always extends inward:
  - `top-left`: right/down
  - `top-right`: left/down
  - `bottom-left`: right/up
  - `bottom-right`: left/up
- Initial physical SVG test: a portrait A6 started from table center and drew
  left/up. Under the app convention this is a `bottom-right` anchor behavior.
- A logical-home SVG adapter is implemented without vendor edits:
  - one shared digest orientation is applied after iDraw rotation/clipping
  - all points remain in positive page bounds
  - logical start coordinates follow the selected corner
  - logical-home changes do not mirror content
  - PLOB metadata prevents duplicate baseline orientation correction
  - reconfiguration invalidates stale prepared snapshots
- Software validation passes for all four corner transforms.
- Three initial A6 physical tests revealed that iDraw digest axes are swapped
  relative to the visual table axes in the A1 portrait setup:
  - digest X mirror changes visual top/bottom
  - digest Y mirror changes visual left/right
- The historical logical-home mirror matrix selected the expected four zones in
  the A1 portrait + A6 physical test:
  - `top-left` -> lower-right
  - `top-right` -> lower-left
  - `bottom-left` -> upper-right
  - `bottom-right` -> upper-left
- A later `bottom-right` test exposed that the matrix also reflected content
  horizontally. Home-specific digest mirrors have now been removed while the
  four start corners remain unchanged. Software validation confirms identical
  geometry for every home.
- The SVG content was observed to be rotated by 180 degrees even before the
  logical-home changes. A separate global digest rotation is now implemented,
  versioned with `idraw_ui_content_orientation=upright-v1` in the PLOB so it is
  idempotent across Play/Resume. Fresh plots now start from the original SVG,
  because replaying the prepared PLOB in `plot` mode caused another vendor-side
  180-degree rotation.
- Final physical validation passes for all four logical homes with the A6 test
  SVG on the A1 portrait setup. Every drawing reaches its expected zone with
  upright, non-reflected content. Preserve this behavior as the portrait
  regression baseline.

Current UI shape:

- `Trace`: `Load SVG`, `Reload`, `Play/Pause/Stop`, quick `Home/Center/Pen Up/Pen Down`, and log view.
- `Jog`: homing, centering, dual jog modes, jog-distance persistence, and
  persisted jog mode selection.
- `Pen`: pen height tuning, live apply toggle, reset, and pen test actions.
- `Draw Options`: speed/acceleration and plot options merged into one page.
- `Machine`: machine model, table orientation, logical home corner, four drawing margins,
  and geometry preview.

## Architecture choices kept for continuity

- UI entrypoint for operations: AppWindow.
- Application backend API boundary: Driver.
- Direct machine serial commands: VendorBridge.
- Plot runtime boundary: Idraw2Facade.
- Concrete internal runtime adapter: Idraw2InternalRuntime.

This separation must stay in place to avoid coupling UI directly to runtime internals.

## Next plans (from current project direction)

1. Post-load SVG preview mode

- After loading an SVG, show a preview of the SVG footprint/gabarit as read from
  the file against the table and current Machine tab choices.

2. Time-estimation refinement

- Improve and calibrate time-estimation calculations.

3. Play/Pause reliability fixes

- Investigate and fix remaining Play/Pause edge cases.
- Specific priority: dot-heavy jobs where points are currently lost.

## Practical note for next contributors

- Keep validating each change on real hardware before locking conventions.
- Keep hardware observations synchronized with docs/hardware_notes.md.
- Keep architecture and decision rationale synchronized with docs/architecture_decisions.md.
