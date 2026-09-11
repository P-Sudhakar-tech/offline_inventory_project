import os
from pathlib import Path

from app.config import app_config

APP_VENDOR = "OfflineInventory"
APP_NAME = "Inventory"


def default_data_dir() -> Path:
    """The suggested default storage folder, offered on first run.

    Kept outside the install directory (ProgramData) so upgrades/reinstalls
    of the application never touch operational data. The admin may choose a
    different folder instead (see app_config.set_database_dir).
    """
    base = os.environ.get("PROGRAMDATA", str(Path.home()))
    return Path(base) / APP_VENDOR / APP_NAME


def data_dir() -> Path:
    """The folder actually in use: the admin-configured one if set, else the default."""
    configured = app_config.get_database_dir()
    path = configured or default_data_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return data_dir() / app_config.DB_FILE_NAME


def backup_dir() -> Path:
    path = data_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path
