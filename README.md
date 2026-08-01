# idraw_ui

Prototype UI and application layer for the new iDraw-based workflow.

This repository is intentionally started as a clean slate, with a clear separation between:

- UI layer
- application/backend layer
- vendor bridge to the iDraw runtime bundle

## Architecture goal

- The UI should talk to a stable application API, not directly to the vendor internals.
- Profiles and machine settings are owned by the application layer.
- Vendor-specific implementation details stay behind the bridge.

## Environment setup (conventional)

This project uses a local virtualenv (`.venv`) and standard pip dependencies.

1. Create and activate local env:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install local Python deps:

```powershell
python -m pip install -r requirements-hw.txt
```

3. Run first hardware test:

```powershell
python scripts\test_tracer_connection.py
```

The test script now talks to DrawCore directly through `pyserial` and does not use
any import or path from the Inkscape extension folder.

## Fork strategy for DrawCore modules

- `plotink` is already available on pip.
- `drawcore_plotink` is not currently published on pip.

If you want to use `drawcore_plotink` as a regular pip dependency, create a dedicated
repository (fork/vendor mirror), add packaging metadata, and install it with:

```powershell
python -m pip install "drawcore_plotink @ git+https://github.com/cfloutier/drawcore_plotink.git@main"
```

Or use the ready-made requirements file:

```powershell
python -m pip install -r requirements-hw-drawcore.txt
```

This removes any runtime dependency on `AppData/Roaming/inkscape/extensions`.

See templates:

- `requirements-hw.txt`
- `requirements-hw-drawcore.txt`
- `requirements-hw-drawcore.example.txt`

