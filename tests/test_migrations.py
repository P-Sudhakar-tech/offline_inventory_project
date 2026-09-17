import sqlite3

from alembic import command

from app.data.migrate import _build_config, run_migrations


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

    Such a database reflects the schema as of the first migration (not the
    current models, which may have moved on since), so it's built by running
    just that first migration and then dropping its version tracking.
    """
    db_path = tmp_path / "inventory.db"
    config = _build_config(db_path)
    initial_revision = "fe4783f90f4f"
    command.upgrade(config, initial_revision)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("DROP TABLE alembic_version")
        conn.commit()
    finally:
        conn.close()

    tables_before = _tables(db_path)
    assert "users" in tables_before
    assert "alembic_version" not in tables_before

    run_migrations(str(db_path))

    tables_after = _tables(db_path)
    assert "alembic_version" in tables_after
    assert tables_after >= tables_before
