# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for idraw_ui standalone distribution.
Build:  pyinstaller idraw_ui.spec
Output: dist/idraw_ui/   (run idraw_ui.exe from there)
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

root = Path(SPECPATH)
src = root / "src"

# ── data files ──────────────────────────────────────────────────────────────
datas = []

# CustomTkinter ships images and themes that must travel with the binary
datas += collect_data_files("customtkinter")

# User-facing defaults bundled in the distribution folder
datas += [
    (str(root / "profiles"), "profiles"),
    (str(root / "test_svg_files"), "test_svg_files"),
]

# Default machine and app-state templates (user settings will be written here at runtime)
datas += [
    (str(root / "settings"), "settings"),
]

# ── hidden imports ───────────────────────────────────────────────────────────
hiddenimports = [
    # serial
    "serial",
    "serial.tools",
    "serial.tools.list_ports",
    "serial.tools.list_ports_common",
    "serial.tools.list_ports_windows",
    # lxml
    "lxml",
    "lxml._elementpath",
    "lxml.etree",
    # yaml
    "yaml",
    # vendor idraw packages (discovered dynamically by the runtime)
    "idraw2_0internal",
    "idraw2_0internal.idraw",
    "drawcore_plotink",
    # tkinter extras
    "tkinter",
    "tkinter.filedialog",
    "xml.etree.ElementTree",
]
hiddenimports += collect_submodules("idraw2_0internal")
hiddenimports += collect_submodules("drawcore_plotink")

# ── analysis ─────────────────────────────────────────────────────────────────
a = Analysis(
    [str(src / "idraw_ui" / "app.py")],
    pathex=[str(src)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "ruff"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="idraw_ui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="idraw_ui",
)
