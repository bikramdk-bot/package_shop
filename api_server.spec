import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

# PyInstaller spec for api_server.py bundling templates and static assets

block_cipher = None

# Resolve project base from current working directory (spec may lack __file__)
BASE = Path.cwd()
SRC_CANDIDATES = [BASE / 'src', BASE]
src_dir = None
for d in SRC_CANDIDATES:
    if (d / 'api_server.py').exists():
        src_dir = d
        break
if src_dir is None:
    # Fallback to BASE/src even if file check fails
    src_dir = BASE / 'src'

# Entry scripts
api_entry = str(src_dir / 'api_server.py')
scanner_entry = str(src_dir / 'scanner_listener.py')

# Include templates/static and config files so dist/ is self-contained
datas = []
for name in ('templates', 'static'):
    p = src_dir / name
    if p.exists():
        datas.append((str(p), name))
for name in ('shop_info.json', 'license.json'):
    p = src_dir / name
    if p.exists():
        datas.append((str(p), name))

hiddenimports = collect_submodules('encodings')

# ---------------- API SERVER BUILD ----------------
a = Analysis(
    [api_entry],
    pathex=[str(src_dir), str(BASE)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='api_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='api_server'
)

# ---------------- SCANNER LISTENER BUILD ----------------

# Minimal datas for scanner (reuse config files); templates/static not required
scanner_datas = []
for name in ('shop_info.json',):
    p = src_dir / name
    if p.exists():
        scanner_datas.append((str(p), name))

a2 = Analysis(
    [scanner_entry],
    pathex=[str(src_dir), str(BASE)],
    binaries=[],
    datas=scanner_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz2 = PYZ(a2.pure, a2.zipped_data, cipher=block_cipher)

exe2 = EXE(
    pyz2,
    a2.scripts,
    [],
    exclude_binaries=True,
    name='scanner_listener',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll2 = COLLECT(
    exe2,
    a2.binaries,
    a2.zipfiles,
    a2.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='scanner_listener'
)
