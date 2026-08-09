# Changelog

All notable changes to this project are recorded here.
Version numbers follow [Semantic Versioning](https://semver.org/).

---

## [0.9.1] — 2026-08-09

### Fixes
- default tab is machine when starting with the app
- added a app_state.yaml default settings 

## [0.9.0] — 2026-08-09

### Added
- US paper sizes in the Marks tab: Tabloid (432 × 279 mm), Letter (279 × 216 mm), Legal (356 × 216 mm), Half Letter (216 × 140 mm)
- Physical pause button now correctly detected — UI shows Paused state and Resume button; previously treated as "Plot finished"
- Standalone distribution build (`build_dist.bat`) producing a versioned ZIP in `release/`; no Python required for end users
- `tag_release.bat` — creates and pushes the git tag matching the current version
- Default machine settings bundled in distribution: iDraw A3, portrait orientation, home at bottom-left corner
- Estimation time displayed in status bar and log after SVG load
- `PyInstaller` added to `requirements.txt`

### Fixed
- `_pause_event` not cleared after stop, causing return-to-start session to abort immediately
- Slider value labels not updating when Reset button is pressed
- Load SVG dialog opening in temp folder after Plot marks

### Changed
- README rewritten for end users (zip/exe distribution); developer setup moved to `docs/developer_notes.md`
- UI poll interval reduced to 500 ms

---

## [0.8.0] — 2026-08-09

### Added
- **Registration marks tab** (Marks) — generates and plots L-shaped corner marks for A0–A6 and Raisin paper formats, portrait and landscape, configurable arm size
- **Physical pause button support** — pressing the machine's hardware button now correctly sets the UI to Paused state and shows Resume
- **Standalone build** — PyInstaller spec (`idraw_ui.spec`) and build script (`build_dist.bat`) to produce a zip archive that runs without Python installed
- **Estimation time display** — estimated plot duration and computation time both shown in status bar and log after load

### Fixed
- Pen heights (`pen_up_height` / `pen_down_height`) now correctly passed to the vendor runtime (`pen_pos_up` / `pen_pos_down`); previously the vendor defaults (0.5 / 5) were always used during plotting
- Physical pause button mid-plot no longer silently treated as "Plot finished"; UI now shows Paused and Resume becomes available
- Slider value labels now update immediately when a Reset button is pressed (label was only refreshed on manual slider movement)
- `_pause_event` now cleared after `stop()` so that subsequent home / return-to-start sessions are not immediately aborted
- Load SVG dialog no longer opens in the temp folder used by Plot marks

### Changed
- UI poll interval reduced to 500 ms (was 400 ms) to lower CPU load on slow machines
- `PyInstaller` added to `requirements.txt` (no separate install needed before building)

---

## [0.7.0] — 2026-08-09

### Added
- **Draw Profile tab** — merged Pen Height and Speed controls into a single tab
- **Reordering combo** moved to the Trace tab (directly below Load SVG)
- **`auto_rotate`** and **`preview`** removed from user profiles (now handled internally per orientation)
- **Machine connectivity pre-check** — Play and Resume immediately report an error if the machine is not reachable instead of silently succeeding
- **Stop returns to pre-plot position** — after pressing Stop, the carriage returns to where it was before Play using the vendor's `resume_type="home"` mechanism

### Fixed
- Portrait pen heights (`pen_up_height` / `pen_down_height`) not applied — identified root cause (options not passed to vendor session)
- `_pause_event` not cleared after stop, causing subsequent sessions to abort immediately

---

## [0.6.0] — 2026-08-08

### Added
- **Landscape orientation** — full physical validation for all 4 home corners (A1 + A6 test SVG)
- **Four drawing margins** — replaced single `my_home_padding_mm` with independent `top`, `bottom`, `left`, `right` integer margins (mm); legacy YAML auto-migrated
- **Set margin from hardware** — Jog tab: go to Home, jog to a boundary, click Set Top / Bottom / Left / Right to record the margin from the physical pen position
- **Jog position display** — live visual position tracking from the last Home in the Jog tab
- **Keyboard arrow keys** — trigger jog when the Jog tab is active
- **Safety: Pen Up before homing** — all Home and Center actions raise the pen before moving; aborts if pen raise fails
- **`_move_and_wait()`** — after positioning moves, the UI waits for the machine to physically settle before showing OK
- **SVG placement preview** in the Trace tab — shows the loaded SVG on the table with home marker, margins, and OUT OF BOUNDS warning

### Fixed
- Landscape orientation: `auto_rotate=True` was causing 90° content rotation; now `False` for landscape
- Landscape `start_pos` formula corrected: `(mirror_x, mirror_y) = (portrait_mirror_y, NOT portrait_mirror_x)`
- Portrait content rotation (global X+Y mirror) now skipped for landscape where the vendor digest arrives already upright
- Slider labels not updating when profile changes programmatically

---

## [0.5.0] — 2026-08-08

### Added
- **Table preview** in Machine tab — live canvas showing table footprint, physical home, logical home marker, and padding zone
- **Visual home modal** — four-corner dialog to select the logical home corner
- **SVG page preview** in Trace tab — proportional page placement on the table, updated on load
- **Log tab** — diagnostic output separated from the main Trace panel
- **Machine tab margin fields** — four integer entry fields (Top / Bottom / Left / Right) replacing the single padding slider
- Portrait SVG orientation validated for all 4 home corners (A1 + A6 test SVG)

### Fixed
- Jog X inversion caused by heuristic sign logic — replaced with deterministic projection-based geometry
- `physical_home` and axis polarity now stored explicitly per machine model

---

## [0.4.0] — 2026-08-07

### Added
- **Dual jog modes** — physical (`+X/-X/+Y/-Y`) and table-relative (`right/left/forward/backward`)
- **Jog mode persistence** — saved in `app_state.yaml`
- **Table-relative jog mapping** — deterministic, based on machine axis metadata
- **Machine settings split** — `machine.yaml` for hardware, `profiles/*.yaml` for draw profiles
- **My home corner** selector with configurable safety padding

---

## [0.3.0] — 2026-08-05 — 2026-08-06

### Added
- **Profile-driven settings** — pen heights, speeds, and acceleration saved per profile
- **Profile selector** in the header bar; profiles created and switched live
- **Last SVG remembered** across restarts (`Reload` button)
- **Estimation pipeline** — fast preview pass calculates expected plot duration
- Speed conversion for estimation (`mm/min → in/s`) to avoid saturation artefacts
- Machine model selection (A0–A4, A1 validated)

### Fixed
- Speed estimation saturation at high `mm/min` values
- Pen reset defaults button not restoring YAML correctly

---

## [0.2.0] — 2026-08-03 — 2026-08-05

### Added
- **CustomTkinter UI** — tabbed interface (Trace, Jog, Pen, Draw Options, Machine)
- **iDraw2 backend facade** — `Idraw2Facade` and `Idraw2InternalRuntime` wrapping the vendor runtime
- **VendorBridge** — pyserial-based serial communication with DrawCore
- **Play / Pause / Stop / Resume** — full plot lifecycle
- **Home / Center** quick actions
- **Pen Up / Pen Down** with configurable Z height

---

## [0.1.0] — 2026-08-01 — 2026-08-02

### Added
- Initial clean-slate project structure (split from `my_axi_draw`)
- `Driver` → `VendorBridge` serial architecture
- Ruff pre-commit linting
- First direct connection tests with the iDraw machine
- AI handoff plan and architecture documentation
