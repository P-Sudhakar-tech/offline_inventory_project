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
