import os
from pathlib import Path

APP_VENDOR = "OfflineInventory"
APP_NAME = "Inventory"


def data_dir() -> Path:
    """Local, per-machine storage directory for the database and backups.

    Kept outside the install directory (ProgramData) so upgrades/reinstalls
    of the application never touch operational data.
    """
    base = os.environ.get("PROGRAMDATA", str(Path.home()))
    path = Path(base) / APP_VENDOR / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return data_dir() / "inventory.db"


def backup_dir() -> Path:
    path = data_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path
