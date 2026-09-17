"""File logging and a global crash handler for the packaged, console-less
desktop app: without this, an unhandled error just makes the app vanish
with no way for the user to report anything actionable.
"""

import logging
import logging.handlers
import sys

from app.config.paths import log_dir

_LOG_FILE_NAME = "app.log"
_MAX_BYTES = 2 * 1024 * 1024
_BACKUP_COUNT = 3

logger = logging.getLogger("app")


def configure_logging() -> None:
    log_path = log_dir() / _LOG_FILE_NAME
    handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def install_excepthook() -> None:
    sys.excepthook = _handle_uncaught_exception


def _handle_uncaught_exception(exc_type, exc_value, exc_tb) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))

    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        if QApplication.instance() is not None:
            QMessageBox.critical(
                None,
                "Unexpected error",
                "An unexpected error occurred. Details were written to:\n"
                f"{log_dir() / _LOG_FILE_NAME}",
            )
    except Exception:
        pass  # showing the dialog is best-effort; the error is already logged
