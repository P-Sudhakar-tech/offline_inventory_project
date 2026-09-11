from pathlib import Path

import pytest

from app.config import app_config


@pytest.fixture(autouse=True)
def isolated_appdata(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    yield


def test_not_configured_until_a_location_is_set():
    assert app_config.is_configured() is False
    assert app_config.get_database_dir() is None
    assert app_config.get_configured_database_path() is None


def test_set_database_dir_persists_across_loads(tmp_path):
    target = tmp_path / "MyInventoryData"
    app_config.set_database_dir(target)

    assert app_config.is_configured() is True
    assert app_config.get_database_dir() == target
    assert app_config.get_configured_database_path() == target / "inventory.db"


def test_set_database_dir_creates_the_folder(tmp_path):
    target = tmp_path / "does" / "not" / "exist" / "yet"
    assert not target.exists()

    app_config.set_database_dir(target)

    assert target.exists()


def test_reconfiguring_overwrites_the_previous_location(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"

    app_config.set_database_dir(first)
    app_config.set_database_dir(second)

    assert app_config.get_database_dir() == second


def test_backup_dir_defaults_to_none():
    assert app_config.get_backup_dir() is None


def test_set_backup_dir_persists_and_creates_folder(tmp_path):
    target = tmp_path / "Backups" / "Inventory"
    app_config.set_backup_dir(target)

    assert app_config.get_backup_dir() == target
    assert target.exists()


def test_backup_retention_defaults_to_fourteen():
    assert app_config.get_backup_retention() == 14


def test_set_backup_retention_persists():
    app_config.set_backup_retention(30)
    assert app_config.get_backup_retention() == 30


def test_database_and_backup_settings_do_not_clobber_each_other(tmp_path):
    db_dir = tmp_path / "db"
    backup_dir = tmp_path / "backup"

    app_config.set_database_dir(db_dir)
    app_config.set_backup_dir(backup_dir)
    app_config.set_backup_retention(5)

    assert app_config.get_database_dir() == db_dir
    assert app_config.get_backup_dir() == backup_dir
    assert app_config.get_backup_retention() == 5
