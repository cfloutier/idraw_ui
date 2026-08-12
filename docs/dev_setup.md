# Developer setup

## Running from source

Requirements: Python 3.10+, Git, access to the `idraw2_internal` sibling repository.

```powershell
# 1 — create and activate the virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # on Linux/macOS: source .venv/bin/activate

# 2 — install dependencies (includes PyInstaller and pre-commit hooks)
python -m pip install -r requirements.txt

# git clone idraw2_internal
git clone https://github.com/cfloutier/idraw2_internal.git ../idraw2_internal

# 3 — install the vendor runtime as editable (development only)
pip install --no-deps -e ../idraw2_internal

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

## Development tooling

Ruff auto-formats and lints Python files on every commit (installed via the
pre-commit hook above).

Run the full test suite:

```powershell
python -m pytest tests -q
```

## Further documentation

- Architecture roles and implementation decisions: `docs/architecture_decisions.md`
- Hardware observations and validated axis mapping: `docs/hardware_notes.md`
- Current project status and next plans: `docs/AI_HANDOFF_PLAN.md`
