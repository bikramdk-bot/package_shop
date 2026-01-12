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

# Entry script
entry_script = str(src_dir / 'api_server.py')

# Include templates and static directories (pick from detected src_dir)
datas = []
for name in ('templates', 'static'):
    p = src_dir / name
    if p.exists():
        datas.append((str(p), name))

hiddenimports = collect_submodules('encodings')

a = Analysis(
    [entry_script],
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
