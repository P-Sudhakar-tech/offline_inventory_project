import sqlite3

import pytest

from app.data.db import create_db_engine, init_db
from app.data.migrate import run_migrations


def _tables(db_path) -> set[str]:
    conn = sqlite3.connect(str(db_path))
    try:
        return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()


def test_run_migrations_creates_full_schema_from_scratch(tmp_path):
    db_path = tmp_path / "inventory.db"
    assert not db_path.exists()

    run_migrations(str(db_path))

    tables = _tables(db_path)
    assert "alembic_version" in tables
    for expected in ("users", "products", "stock_transactions", "audit_logs"):
        assert expected in tables


def test_run_migrations_is_idempotent(tmp_path):
    db_path = tmp_path / "inventory.db"
    run_migrations(str(db_path))
    run_migrations(str(db_path))  # must not raise on an already-current DB

    assert "alembic_version" in _tables(db_path)


def test_run_migrations_adopts_a_pre_alembic_database(tmp_path):
    """A database created by an older version of the app (before Alembic
    was introduced) has all the application tables from create_all but no
    alembic_version table. Migrations must adopt it in place rather than
    trying to re-create tables that already exist.
    """
    db_path = tmp_path / "inventory.db"
    engine = create_db_engine(db_path=str(db_path))
    init_db(engine)
    engine.dispose()

    tables_before = _tables(db_path)
    assert "users" in tables_before
    assert "alembic_version" not in tables_before

    run_migrations(str(db_path))

    tables_after = _tables(db_path)
    assert "alembic_version" in tables_after
    assert tables_after >= tables_before
