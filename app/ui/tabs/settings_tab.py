import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import app_config
from app.config.paths import backup_dir, database_path
from app.services.backup import (
    BackupError,
    RestoreError,
    create_backup,
    list_backups,
    prune_backups,
    restore_backup,
)


def _format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)
        layout.addWidget(self._build_database_section())
        layout.addWidget(self._build_backup_section())
        layout.addStretch()

        self.refresh_backups()

    # --- Database location --------------------------------------------

    def _build_database_section(self) -> QWidget:
        section = QWidget()
        title = QLabel("Database Location")
        title.setObjectName("SectionTitle")

        self.db_path_edit = QLineEdit(str(database_path()))
        self.db_path_edit.setReadOnly(True)

        change_btn = QPushButton("Change Location...")
        change_btn.setObjectName("PrimaryButton")
        change_btn.clicked.connect(self._change_database_location)

        note = QLabel(
            "Changing this moves the database file to the new folder. "
            "Restart the application afterwards for the change to take effect."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Current location", self.db_path_edit)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addWidget(change_btn)
        layout.addWidget(note)
        return section

    def _change_database_location(self):
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
        self.db_path_edit.setText(str(new_db_path))
        QMessageBox.information(
            self,
            "Location updated",
            "Database location updated. Please restart the application for this to take effect.",
        )

    # --- Backup & restore ------------------------------------------------

    def _build_backup_section(self) -> QWidget:
        section = QWidget()
        title = QLabel("Backup & Restore")
        title.setObjectName("SectionTitle")

        self.backup_dir_edit = QLineEdit(str(backup_dir()))
        self.backup_dir_edit.setReadOnly(True)
        change_folder_btn = QPushButton("Change Backup Folder...")
        change_folder_btn.clicked.connect(self._change_backup_folder)

        self.retention_spin = QSpinBox()
        self.retention_spin.setRange(1, 365)
        self.retention_spin.setValue(app_config.get_backup_retention())
        self.retention_spin.valueChanged.connect(self._on_retention_changed)

        backup_now_btn = QPushButton("Backup Now")
        backup_now_btn.setObjectName("PrimaryButton")
        backup_now_btn.clicked.connect(self._backup_now)

        restore_btn = QPushButton("Restore Selected")
        restore_btn.clicked.connect(self._restore_selected)

        folder_row = QHBoxLayout()
        folder_row.addWidget(self.backup_dir_edit)
        folder_row.addWidget(change_folder_btn)

        form = QFormLayout()
        form.addRow("Backup folder", folder_row)
        form.addRow("Keep this many backups", self.retention_spin)

        note = QLabel(
            "A backup is also taken automatically once per day when an "
            "admin signs in. Restoring requires an application restart."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)

        self.backups_table = QTableWidget(0, 2)
        self.backups_table.setHorizontalHeaderLabels(["Backup", "Size"])
        self.backups_table.horizontalHeader().setStretchLastSection(True)
        self.backups_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.backups_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.backups_table.setAlternatingRowColors(True)
        self.backups_table.setMaximumHeight(220)

        btn_row = QHBoxLayout()
        btn_row.addWidget(backup_now_btn)
        btn_row.addWidget(restore_btn)
        btn_row.addStretch()

        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addLayout(btn_row)
        layout.addWidget(self.backups_table)
        return section

    def refresh_backups(self):
        self._backups = list_backups(backup_dir())
        self.backups_table.setRowCount(len(self._backups))
        for i, path in enumerate(self._backups):
            mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            self.backups_table.setItem(i, 0, QTableWidgetItem(f"{path.name}  ({mtime})"))
            self.backups_table.setItem(i, 1, QTableWidgetItem(_format_size(path.stat().st_size)))

    def _on_retention_changed(self, value: int):
        app_config.set_backup_retention(value)

    def _change_backup_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose backup folder", str(backup_dir()))
        if not folder:
            return
        app_config.set_backup_dir(Path(folder))
        self.backup_dir_edit.setText(folder)
        self.refresh_backups()

    def _backup_now(self):
        try:
            path = create_backup(database_path(), backup_dir())
            prune_backups(backup_dir(), keep=app_config.get_backup_retention())
        except BackupError as exc:
            QMessageBox.warning(self, "Backup failed", str(exc))
            return
        self.refresh_backups()
        QMessageBox.information(self, "Backup created", f"Saved to {path}")

    def _restore_selected(self):
        row = self.backups_table.currentRow()
        if row < 0 or row >= len(self._backups):
            QMessageBox.information(self, "No selection", "Select a backup to restore.")
            return
        backup_path = self._backups[row]

        confirm = QMessageBox.question(
            self,
            "Confirm restore",
            f"Restore '{backup_path.name}'?\n\n"
            "This replaces the current database. The application must be "
            "restarted afterwards.",
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            restore_backup(backup_path, database_path())
        except RestoreError as exc:
            QMessageBox.warning(self, "Restore failed", str(exc))
            return

        QMessageBox.information(
            self,
            "Restore complete",
            "Database restored. Please restart the application now.",
        )
