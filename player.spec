# -*- mode: python ; coding: utf-8 -*-
# Build: pyinstaller player.spec --noconfirm
a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[("bin/libmpv-2.dll", ".")],
    datas=[("icon.svg", ".")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ENILINE_Media_Player",
    debug=False,
    icon="icon.png",
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ENILINE_Media_Player",
)