# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


root = Path(SPECPATH)
datas = [
    (str(root / "src" / "ls900_biometry" / "models"), "ls900_biometry/models"),
    (str(root / "src" / "ls900_biometry" / "assets"), "ls900_biometry/assets"),
]

a = Analysis(
    [str(root / "desktop_launcher.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=["PySide6.QtSvg"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PySide6.QtNetwork", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtQml", "PySide6.QtQuick", "Flask", "pystray"],
    noarchive=False,
    optimize=0,
)
# Qt 6 on Windows uses the Windows ICU API. A developer's PATH can contain
# incompatible Conda/Poppler ICU DLLs with the same names; never bundle those.
# Use the supported Windows system libraries instead of shadowing them.
windows_icu = {"icu.dll", "icuuc.dll", "icuin.dll", "icudt.dll"}
a.binaries = [entry for entry in a.binaries
              if Path(entry[0]).name.lower() not in windows_icu]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OcularSpan",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(root / "assets" / "app_icon.ico")],
    version=str(root / "build_tools" / "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="OcularSpan",
)
