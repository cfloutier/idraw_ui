# Developer notes

## Running from source

Requirements: Python 3.10+, Git, access to the `idraw2_internal` sibling repository.

```powershell
# 1 — create and activate the virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # on Linux/macOS: source .venv/bin/activate

# 2 — install dependencies (includes PyInstaller and pre-commit hooks)
python -m pip install -r requirements.txt

# 3 — install the vendor runtime as editable (development only)
pip install --no-deps -e C:\dev\__tracer\idraw2_internal

# 4 — install the pre-commit hooks
python -m pre_commit install

# 5 — launch
.\run.bat   # or: PYTHONPATH=src python -m idraw_ui.app
```

## Building a distributable ZIP

```powershell
.\build_dist.bat
```

Produces `idraw_ui_v<version>.zip` in the project root. End users unzip and
double-click `idraw_ui.exe` — no Python required.

The script temporarily installs `idraw2_0internal` as a regular package (not
editable) so PyInstaller can find all its files, then reinstalls it as editable
when done.

---

## Architecture goal

- The UI talks to a stable application API, not directly to vendor internals.
- Profiles and machine settings are owned by the application layer.
- Vendor-specific implementation details stay behind the bridge.

### Layer boundaries

```
AppWindow → Driver → Idraw2Facade → Idraw2InternalRuntime → idraw2_0internal
                   → VendorBridge (serial / DrawCore)
```

## DrawCore dependency

`drawcore_plotink` is installed from the public GitHub repository through
`requirements.txt`, which removes any runtime dependency on
`AppData/Roaming/inkscape/extensions`.

## Profile-driven backend config

The UI uses a persistent settings layer backed by YAML files.
Active profile and profile values are saved automatically as the user changes them.

### Files involved

- `settings/app_state.yaml` — active profile, jog mode, last SVG path/folder.
- `settings/machine.yaml` — machine configuration.
- `profiles/*.yaml` — individual plot profiles.

### Speed units and estimation

The UI exposes speed sliders as `mm/min`. During estimation (preview mode) these
values are converted to the runtime scale expected by the iDraw internal estimator:

```
in/s = mm/min / (25.4 × 60)
```

Without conversion, large UI speed values produce nearly identical estimated
times (saturation effect). Conversion is applied only for estimation sessions;
real plotting sessions keep the raw profile values.

## SVG orientation pipeline

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

## Recent progress (Aug 2026)

- Portrait and landscape both fully validated for all 4 home corners (A1 + A6).
- Four asymmetric drawing margins replace the single padding value.
- Jog tab: live position display and Set Margin buttons for margin setup from hardware.
- All Home/Center actions raise pen before homing; `_move_and_wait()` delays UI
  status until machine physically settles.
- `Draw Profile` tab merges Speed and Pen Height controls.
- `auto_rotate` and `preview` removed from profiles (handled internally).

## Next milestones

1. Enforce bounds so transformed SVG cannot leave the usable plotter area.
2. Validate landscape mapping for all machines beyond A1.
3. Positioning-mark tool to draw page placement marks on the table.
4. Refine time-estimation calculations.
5. Investigate Play/Pause edge cases in dot-heavy drawings.

## Development tooling

```powershell
python -m pip install pre-commit
python -m pre_commit install
```

Ruff auto-formats and lints Python files on every commit.

Run the full test suite:

```powershell
python -m pytest tests -q
```
