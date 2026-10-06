# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


root = Path(SPECPATH)
datas = [
    (str(root / "src" / "ls900_biometry" / "templates"), "ls900_biometry/templates"),
    (str(root / "src" / "ls900_biometry" / "static"), "ls900_biometry/static"),
    (str(root / "src" / "ls900_biometry" / "models"), "ls900_biometry/models"),
    (str(root / "src" / "ls900_biometry" / "assets"), "ls900_biometry/assets"),
]

a = Analysis(
    [str(root / "desktop_launcher.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=["pystray._win32"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LS900 Biometry Analyzer",
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
    name="LS900 Biometry Analyzer",
)
