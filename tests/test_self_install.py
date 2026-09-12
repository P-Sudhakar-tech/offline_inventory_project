from pathlib import Path

import pytest

from app.setup import self_install


def test_is_frozen_false_in_dev_and_test_runs():
    assert self_install.is_frozen() is False


def test_install_dir_uses_localappdata(monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\Someone\AppData\Local")
    result = self_install.install_dir()
    assert result == Path(r"C:\Users\Someone\AppData\Local\Programs") / self_install.APP_NAME


@pytest.fixture()
def scratch_registry_key():
    """A throwaway HKCU subkey so these tests never touch the real
    production uninstall entry the packaged app registers under."""
    key_path = r"Software\OfflineInventoryTest\SelfInstallTests"
    yield key_path
    self_install._remove_uninstall_entry(key_path)


def test_uninstall_entry_round_trip(scratch_registry_key):
    fake_exe = Path(r"C:\Users\Someone\AppData\Local\Programs\Test App\InventoryManager.exe")

    assert self_install.is_installed(scratch_registry_key) is False

    self_install._register_uninstall_entry(fake_exe, scratch_registry_key)
    assert self_install.is_installed(scratch_registry_key) is True

    self_install._remove_uninstall_entry(scratch_registry_key)
    assert self_install.is_installed(scratch_registry_key) is False


def test_removing_nonexistent_uninstall_entry_does_not_raise(scratch_registry_key):
    self_install._remove_uninstall_entry(scratch_registry_key)  # already absent; must not raise
