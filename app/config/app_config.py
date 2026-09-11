import json
import os
from pathlib import Path

CONFIG_VENDOR = "OfflineInventory"
CONFIG_FILE_NAME = "config.json"
DB_FILE_NAME = "inventory.db"


def config_dir() -> Path:
    """Where the small pointer config file lives.

    This uses the per-user APPDATA folder rather than ProgramData: it must
    always be writable without admin rights, since it is read before we know
    where the (admin-configurable) database itself lives.
    """
    base = os.environ.get("APPDATA", str(Path.home()))
    path = Path(base) / CONFIG_VENDOR
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_file_path() -> Path:
    return config_dir() / CONFIG_FILE_NAME


def is_configured() -> bool:
    return config_file_path().exists()


def load_config() -> dict:
    path = config_file_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_config(data: dict) -> None:
    config_file_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_database_dir() -> Path | None:
    value = load_config().get("database_dir")
    return Path(value) if value else None


def set_database_dir(directory: Path) -> None:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    config = load_config()
    config["database_dir"] = str(directory)
    save_config(config)


def get_configured_database_path() -> Path | None:
    directory = get_database_dir()
    return (directory / DB_FILE_NAME) if directory else None
