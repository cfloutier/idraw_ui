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
- Persistent profile management is now implemented.
- Profile changes are saved immediately as the user edits them.
- Creating a new profile from the UI is now supported.

Additional behavior now in place:

- Manual actions run with auto connect -> action -> auto disconnect.
- Plot runtime can take control without requiring manual disconnect first.
- Manual action stop is handled as best effort via disconnect.
- The active profile is persisted through `settings/app_state.yaml`.
- Profile files are stored under `profiles/` and reloaded on startup.

## Architecture choices kept for continuity

- UI entrypoint for operations: AppWindow.
- Application backend API boundary: Driver.
- Direct machine serial commands: VendorBridge.
- Plot runtime boundary: Idraw2Facade.
- Concrete internal runtime adapter: Idraw2InternalRuntime.

This separation must stay in place to avoid coupling UI directly to runtime internals.

## Next plans (from current project direction)

1. Profile management refinements:

- add rename/delete profile actions in the UI
- add richer profile naming validation
- expose machine settings in the same persistence flow

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
