import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import app_config
from app.config.paths import database_path


class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        title = QLabel("Database Location")
        title.setObjectName("SectionTitle")

        self.path_edit = QLineEdit(str(database_path()))
        self.path_edit.setReadOnly(True)

        change_btn = QPushButton("Change Location...")
        change_btn.setObjectName("PrimaryButton")
        change_btn.clicked.connect(self._change_location)

        note = QLabel(
            "Changing this moves the database file to the new folder. "
            "Restart the application afterwards for the change to take effect."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Current location", self.path_edit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addWidget(change_btn)
        layout.addWidget(note)
        layout.addStretch()

    def _change_location(self):
        current_dir = database_path().parent
        folder = QFileDialog.getExistingDirectory(self, "Choose new database folder", str(current_dir))
        if not folder:
            return

        new_dir = Path(folder)
        if new_dir == current_dir:
            return

        new_db_path = new_dir / app_config.DB_FILE_NAME
        current_db_path = database_path()

        if new_db_path.exists():
            answer = QMessageBox.question(
                self,
                "Existing database found",
                f"'{new_db_path}' already contains a database.\n\n"
                "Use that existing database instead of the current one? "
                "(Your current data at the old location will not be touched or deleted.)",
            )
            if answer != QMessageBox.Yes:
                return
        else:
            try:
                new_dir.mkdir(parents=True, exist_ok=True)
                if current_db_path.exists():
                    shutil.copy2(current_db_path, new_db_path)
            except OSError as exc:
                QMessageBox.warning(self, "Could not move database", str(exc))
                return

        app_config.set_database_dir(new_dir)
        self.path_edit.setText(str(new_db_path))
        QMessageBox.information(
            self,
            "Location updated",
            "Database location updated. Please restart the application for this to take effect.",
        )
