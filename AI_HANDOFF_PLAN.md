# AI Handoff: Current State, Decisions, and Next Steps

## 1) Mission and product direction

The project `idraw_ui` is a clean-slate application for iDraw/DrawCore control.
The architecture target is strict separation:

- UI layer
- application/backend layer
- vendor/hardware bridge layer

The key strategic decision is to avoid direct runtime dependency on Inkscape extension folders.

## 2) Repository status

### Main app repository

- Repository: `idraw_ui`
- Current branch: `main`
- Recent local commit: `a654c67` (dependency cleanup)

### Vendor repository created

- Repository: `drawcore_plotink`
- Remote: `https://github.com/cfloutier/drawcore_plotink.git`
- Branch: `main`
- Current head: `296598c`

`drawcore_plotink` is now installable via pip from GitHub.

## 3) Runtime dependency strategy (finalized)

Single source of truth for runtime environment:

- `requirements.txt`

Current runtime dependencies:

- `pyserial>=3.5`
- `lxml>=6.1.0`
- `drawcore_plotink @ git+https://github.com/cfloutier/drawcore_plotink.git@main`

`pyproject.toml` keeps package metadata and intentionally avoids duplicating runtime dependencies to prevent drift.

## 4) Hardware validation already completed

A direct hardware smoke test exists and is passing:

- Script: `scripts/test_tracer_connection.py`

Validated behavior:

- DrawCore-compatible port detection by VID/PID
- Serial open at 115200
- Firmware handshake (`V`)
- Status query (`?`)
- Home command (`$H`)
- Status query after home
- Pen up / pen down movements

Observed successful run on COM5 with expected status transitions, HOME acknowledged, and pen up/down commands validated.

## 5) Why no Inkscape path dependency remains

The test script uses plain `pyserial` and direct DrawCore protocol commands.
No runtime path to `AppData/Roaming/inkscape/extensions` is required.

This was a deliberate architectural move to make the app portable and reproducible in a normal Python environment.

## 6) Position on `plotink` vs `drawcore_plotink`

- `plotink` (PyPI) is general-purpose and historically EBB/AxiDraw oriented.
- `drawcore_plotink` is the DrawCore/iDraw-specialized layer used for this hardware stack.

For this project baseline, `plotink` is not required.

## 7) `idraw2_0internal` status and plan

Source reference exists in Inkscape dependencies:

- `idraw_deps/idraw2_0internal`

What it contains:

- rich plotting pipeline (digest, optimization, resume, preview, plot modes)
- strong coupling to Inkscape runtime (`inkex`, option parser, document model)

Decision:

- do not make `idraw2_0internal` a hard runtime dependency of `idraw_ui` now
- keep the app backend headless/minimal first
- treat `idraw2_0internal` as a future advanced extraction target

Planned path for that future:

1. Create a dedicated public fork repository for `idraw2_0internal` (or equivalent naming).
2. Preserve and document licensing constraints (GPL context in that tree).
3. Identify modules that can be consumed headless with minimal `inkex` coupling.
4. Expose only necessary advanced capabilities behind a stable bridge API.

## 8) Current code maturity in `idraw_ui`

### Implemented

- scaffolding for package and folders
- app entrypoint placeholder
- backend data models
- concrete backend bridge for connect/disconnect/status/home/pen up/down
- driver wiring for real hardware actions
- hardware smoke test script

### Still placeholders

- `src/idraw_ui/backend/driver.py`: some higher-level plotting workflow actions remain to be expanded
- `src/idraw_ui/backend/vendor_bridge.py`: advanced motion/plotting capabilities can still be added later
- `src/idraw_ui/ui/app_window.py`: UI remains minimal and can be extended once workflow needs grow

## 9) Next execution plan (phased)

### Phase A: real backend bridge

Completed: a concrete hardware bridge is now implemented in backend for:

- connect/disconnect
- read status
- home
- pen raise/lower
- robust error handling and resource cleanup

### Phase B: wire driver to real bridge

Completed: `Driver` is now wired to the real bridge for the core machine-control actions, with progress state updated coherently.

### Phase C: profile/config integration

Read profile values and apply relevant runtime parameters in a controlled way.

### Phase D: UI MVP

Completed: a minimal operational UI panel is now available with:

- connect
- status display
- home
- pen up/down

### Phase E: advanced pipeline (optional)

Evaluate selective import/fork extraction from `idraw2_0internal` for advanced plot/resume features.

## 10) Operational constraints and conventions

- Keep a single runtime dependency entrypoint (`requirements.txt`).
- Avoid hardcoded machine-specific paths.
- Keep hardware-specific code behind backend bridge boundaries.
- Validate behavior on real hardware for each backend milestone.

## 11) Immediate handoff checklist for next AI agent

1. Confirm environment with `pip install -r requirements.txt`.
2. Confirm hardware baseline with `python scripts/test_tracer_connection.py`.
3. Implement bridge class in backend using installed `drawcore_plotink` APIs.
4. Replace `Driver` placeholders with real commands.
5. Add minimal tests for backend behavior and failure handling.
6. Keep UI changes minimal until backend behavior is stable.

## 12) Scope boundaries for now

In scope now:

- stable direct machine control from backend and simple UI triggers

Out of scope now:

- full Inkscape-compatible plotting pipeline
- complete resume/replot feature parity with historical extension behavior

---

This document is intended as a complete passation note for any AI or human contributor picking up the project from this point.
