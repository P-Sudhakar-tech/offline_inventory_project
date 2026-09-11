# PyInstaller spec for the Offline Inventory Management System.
#
# Build with:  pyinstaller inventory_manager.spec
#
# Two kinds of data must be bundled as real files on disk (not compiled
# into the PYZ archive), because they are read by file path at runtime
# rather than imported as Python modules:
#   - resources/style.qss, read directly by main.py
#   - app/data/migrations/**, scanned by Alembic's ScriptDirectory to find
#     env.py and every versions/*.py revision file

import os

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

datas = [
    ("resources/style.qss", "resources"),
    ("app/data/migrations/env.py", "app/data/migrations"),
    ("app/data/migrations/script.py.mako", "app/data/migrations"),
]

versions_dir = os.path.join("app", "data", "migrations", "versions")
for filename in os.listdir(versions_dir):
    if filename.endswith(".py"):
        datas.append((os.path.join(versions_dir, filename), os.path.join(versions_dir)))

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "alembic",
        "sqlalchemy.dialects.sqlite",
        # Only imported inside app/data/migrations/env.py, which Alembic
        # execs by file path rather than a normal import - PyInstaller's
        # static analysis never sees that import, so it must be listed here.
        "logging.config",
        # env.py also does `from app.data.models import Base`. That happens
        # to be reachable through main.py's own import graph today, but
        # relying on that would silently break the frozen build the next
        # time someone refactors an unrelated import - so bundle the whole
        # app package explicitly instead of hoping it stays reachable.
        *collect_submodules("app"),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="InventoryManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# One-dir build: a real, inspectable folder of files rather than a
# self-extracting single exe (avoids onefile's temp-extraction step and
# the antivirus false positives that step commonly triggers).
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="InventoryManager",
)
