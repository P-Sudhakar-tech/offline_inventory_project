import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# A table that has existed since the very first migration; its presence
# without alembic_version means the database predates migration tracking.
_LEGACY_MARKER_TABLE = "users"


class MigrationError(Exception):
    pass


def _build_config(db_path) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


def _is_pre_migration_database(db_path: Path) -> bool:
    """True for a database created before Alembic was introduced: it has
    application tables (built via Base.metadata.create_all) but no
    alembic_version table to say which revision it is at.
    """
    if not db_path.exists():
        return False
    conn = sqlite3.connect(str(db_path))
    try:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()
    return _LEGACY_MARKER_TABLE in tables and "alembic_version" not in tables


def run_migrations(db_path) -> None:
    """Brings the database at db_path up to the latest schema version,
    creating it from scratch if it does not exist yet.

    Built without relying on alembic.ini (its path would be wrong once the
    app is frozen by PyInstaller), so every option Alembic needs is set
    programmatically instead.

    A database that already exists from before migrations were introduced
    (application tables present, no alembic_version table) is stamped at
    the initial revision instead of re-run through it, since create_all
    already built exactly that schema; anything newer is then applied
    normally on top.
    """
    db_path = Path(db_path)
    config = _build_config(db_path)
    try:
        if _is_pre_migration_database(db_path):
            initial_revision = ScriptDirectory.from_config(config).get_bases()[0]
            command.stamp(config, initial_revision)
        command.upgrade(config, "head")
    except Exception as exc:  # alembic raises plain Exception/CommandError subtypes
        raise MigrationError(f"Failed to prepare the database: {exc}") from exc
