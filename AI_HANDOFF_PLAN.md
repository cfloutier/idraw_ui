# AI Handoff Plan

## Current validated status

The following points are now implemented and validated on real tests:

- Play was tested and validated.
- Status handling in UI is OK (including working states and feedback flow).
- Manual actions added and validated:
  - Home
  - Center
  - Pen Up
  - Pen Down
  - Jog controls

Additional behavior now in place:

- Manual actions run with auto connect -> action -> auto disconnect.
- Plot runtime can take control without requiring manual disconnect first.
- Manual action stop is handled as best effort via disconnect.

## Architecture choices kept for continuity

- UI entrypoint for operations: AppWindow.
- Application backend API boundary: Driver.
- Direct machine serial commands: VendorBridge.
- Plot runtime boundary: Idraw2Facade.
- Concrete internal runtime adapter: Idraw2InternalRuntime.

This separation must stay in place to avoid coupling UI directly to runtime internals.

## Next plans (from current project direction)

1. Profile management like legacy project behavior:

- load profile
- auto save profile updates

2. Table calibration management:

- table size setup
- preferred home selection

3. SVG rotation handling:

- rotate SVG automatically according to chosen home/calibration orientation

4. Movement speed tuning:

- improve controls and persistence for travel and plotting speeds

## Practical note for next contributors

- Keep validating each change on real hardware before locking conventions.
- Keep hardware observations synchronized with docs/hardware_notes.md.
- Keep architecture and decision rationale synchronized with docs/architecture_decisions.md.
