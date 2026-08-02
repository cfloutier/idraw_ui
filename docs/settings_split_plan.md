# Settings split plan for idraw_ui

## Goal

Separate stable machine installation settings from drawing-specific profile settings, while keeping a small app-state file for UI persistence.

## Current state in idraw_ui

Today, one file (`profiles/default.yaml`) mixes machine and drawing concerns.

Current mixed keys include:

- machine-ish: `machine_model`
- profile-ish: `pen_up_height`, `pen_down_height`, `speed_penup`, `speed_pendown`, `accel`, `auto_rotate`, `reordering`, `preview`, `digest`
- bridge extras from `field`: `port`, `baudrate`, `serial_timeout`, `pen_up_command`, `pen_down_command`, `pen_move_speed`

## Reference pattern observed in my_axi_draw

my_axi_draw effectively uses three buckets:

- internal app state (`internal.yml`)
- machine calibration/config (`plotter.yml`)
- drawing/pen profile (`default.yml`, `posca.yml`, etc.)

Important caveat in old implementation:

- Generic `setattr` loading and full `__dict__` saving can leak keys between buckets.

idraw_ui should keep the same conceptual separation, but with strict schemas per file.

## Proposed files

- `settings/machine.yaml`
- `profiles/default.yaml` and `profiles/<name>.yaml`
- `settings/app_state.yaml`

## Proposed data models

### MachineSettings (stable after installation)

- `name: str` (default: `machine-default`)
- `machine_model: str`
- `port: str | null`
- `baudrate: int`
- `serial_timeout: float`
- `native_res_factor: float | null`
- `switch_xy: bool | null`
- `x_travel_mm: float | null`
- `y_travel_mm: float | null`

Notes:

- The first milestone can keep only `machine_model`, `port`, `baudrate`, `serial_timeout` and add calibration fields later.

### PlotProfile (changes per drawing/tool)

- `name: str`
- `pen_up_height: float`
- `pen_down_height: float`
- `pen_move_speed: float | null`
- `speed_penup: float`
- `speed_pendown: float`
- `accel: float`
- `auto_rotate: bool`
- `reordering: int`
- `preview: bool`
- `digest: int`
- `pen_up_command: str | null`
- `pen_down_command: str | null`

### AppState (UI/session persistence)

- `active_profile: str`
- `last_svg_file: str | null`
- `last_folder: str | null`

## Key-by-key mapping from current idraw_ui

From `profiles/default.yaml` today:

Move to `settings/machine.yaml`:

- `machine_model`

Keep in `profiles/<name>.yaml`:

- `name`
- `pen_up_height`
- `pen_down_height`
- `speed_penup`
- `speed_pendown`
- `accel`
- `auto_rotate`
- `reordering`
- `preview`
- `digest`

From profile extras currently read via `field` in Driver:

Move to `settings/machine.yaml`:

- `port`
- `baudrate`
- `serial_timeout`

Keep in `profiles/<name>.yaml`:

- `pen_up_command`
- `pen_down_command`
- `pen_move_speed`

## Runtime merge rule

Build an effective runtime config as:

1. start from defaults in code
2. apply `MachineSettings`
3. apply `PlotProfile`

Conflict policy:

- machine-owned keys are never overridden by profile files
- profile-owned keys are always resolved from active profile

## Validation policy

- Unknown keys are rejected with explicit error by default.

## Migration plan (direct cutover)

1. Add new typed models and loaders for `MachineSettings`, `PlotProfile`, `AppState`.
2. Update `Driver` constructor to accept `(machine_settings, plot_profile)`.
3. Add tests:
   - ownership rules for each key
   - merge precedence
4. Add initial files:
   - `settings/machine.yaml`
   - `settings/app_state.yaml`
   - updated `profiles/default.yaml`
5. Remove legacy `MachineProfile` path once all call sites are migrated.

## Immediate next step

Implement step 1 and step 2 (new models/loaders + Driver wiring) with tests first.
