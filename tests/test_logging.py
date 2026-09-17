import logging

import pytest

from app.config import app_config
from app.logging_setup import configure_logging, install_excepthook, logger


@pytest.fixture()
def isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path / "config"))
    app_config.set_database_dir(tmp_path / "data")
    yield tmp_path / "data"


@pytest.fixture(autouse=True)
def restore_root_logger():
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level
    yield
    for handler in list(root.handlers):
        if handler not in original_handlers:
            root.removeHandler(handler)
            handler.close()
    root.setLevel(original_level)


@pytest.fixture(autouse=True)
def restore_excepthook():
    import sys
    original = sys.excepthook
    yield
    sys.excepthook = original


def test_configure_logging_creates_log_file_and_writes(isolated_data_dir):
    configure_logging()

    logger.info("hello from test")
    for handler in logging.getLogger().handlers:
        handler.flush()

    log_path = isolated_data_dir / "logs" / "app.log"
    assert log_path.exists()
    assert "hello from test" in log_path.read_text(encoding="utf-8")


def test_install_excepthook_sets_a_callable(isolated_data_dir):
    import sys

    configure_logging()
    install_excepthook()

    assert callable(sys.excepthook)
    assert sys.excepthook is not sys.__excepthook__

    try:
        raise ValueError("boom")
    except ValueError:
        exc_type, exc_value, exc_tb = __import__("sys").exc_info()

    sys.excepthook(exc_type, exc_value, exc_tb)  # must not raise

    for handler in logging.getLogger().handlers:
        handler.flush()
    log_path = isolated_data_dir / "logs" / "app.log"
    assert "Unhandled exception" in log_path.read_text(encoding="utf-8")
