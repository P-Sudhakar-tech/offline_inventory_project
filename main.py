import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from app.config import app_config
from app.config.paths import database_path
from app.data.migrate import MigrationError, run_migrations
from app.data.session import new_session
from app.security.session_context import set_current_user
from app.services.auth import has_any_user
from app.ui.dialogs.database_location_dialog import DatabaseLocationDialog
from app.ui.dialogs.first_run_setup_dialog import FirstRunSetupDialog
from app.ui.dialogs.login_dialog import LoginDialog
from app.ui.main_window import MainWindow


def load_stylesheet() -> str:
    style_path = Path(__file__).parent / "resources" / "style.qss"
    return style_path.read_text(encoding="utf-8")


def ensure_database_configured() -> bool:
    """Asks where to store the database the very first time the app runs on
    a machine. Must happen before any DB access (new_session()), since that
    is what pins the database file location for the rest of the process.
    Returns False if the user cancelled out.
    """
    if app_config.is_configured():
        return True
    dialog = DatabaseLocationDialog()
    return dialog.exec() == QDialog.Accepted


def prepare_database() -> bool:
    """Brings the configured database up to the current schema version,
    creating it from scratch if it does not exist yet. Runs once at
    startup, before any part of the app opens a session. Returns False if
    migration failed, in which case the app should not proceed.
    """
    try:
        run_migrations(database_path())
        return True
    except MigrationError as exc:
        QMessageBox.critical(None, "Database error", str(exc))
        return False


def sign_in():
    """Runs first-run admin setup if needed, then the login dialog.
    Returns the authenticated User, or None if the user cancelled out.
    """
    with new_session() as session:
        needs_setup = not has_any_user(session)

    if needs_setup:
        setup_dialog = FirstRunSetupDialog()
        if setup_dialog.exec() != QDialog.Accepted:
            return None

    login_dialog = LoginDialog()
    if login_dialog.exec() != QDialog.Accepted:
        return None
    return login_dialog.authenticated_user


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet())

    if not ensure_database_configured():
        sys.exit(0)

    if not prepare_database():
        sys.exit(1)

    while True:
        user = sign_in()
        if user is None:
            sys.exit(0)

        set_current_user(user)
        window = MainWindow(user)
        window.show()
        app.exec()
        set_current_user(None)

        if not window.logout_requested:
            sys.exit(0)


if __name__ == "__main__":
    main()
