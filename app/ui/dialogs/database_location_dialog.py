from pathlib import Path

from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from app.config import app_config
from app.config.paths import default_data_dir


class DatabaseLocationDialog(QDialog):
    """Shown once, the very first time the app runs on a machine: asks
    where the local database should live. If the chosen folder already
    contains an inventory.db (e.g. pointing back at a previous install's
    data folder), that existing database is used as-is rather than
    replaced, since table creation is additive and never destructive.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Location")
        self.setMinimumWidth(460)

        self.default_dir = default_data_dir()
        self.selected_dir = self.default_dir

        title = QLabel("Where should this app store its data?")
        title.setObjectName("PageTitle")
        title.setWordWrap(True)

        subtitle = QLabel(
            "This machine keeps all inventory data locally, in one folder. "
            "You can use the recommended location or choose your own "
            "(for example, a folder on another drive)."
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)

        self.default_radio = QRadioButton(f"Use recommended location\n{self.default_dir}")
        self.custom_radio = QRadioButton("Use a custom folder")
        self.default_radio.setChecked(True)

        group = QButtonGroup(self)
        group.addButton(self.default_radio)
        group.addButton(self.custom_radio)
        self.default_radio.toggled.connect(self._on_mode_changed)

        self.path_edit = QLineEdit(str(self.default_dir))
        self.path_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)

        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit)
        path_row.addWidget(browse_btn)

        self.status_label = QLabel("")
        self.status_label.setObjectName("Muted")
        self.status_label.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Ok).setText("Continue")
        buttons.button(QDialogButtonBox.Ok).setObjectName("PrimaryButton")
        buttons.accepted.connect(self._on_accept)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(6)
        layout.addWidget(self.default_radio)
        layout.addWidget(self.custom_radio)
        layout.addLayout(path_row)
        layout.addWidget(self.status_label)
        layout.addWidget(buttons)

        self._on_mode_changed()

    def _on_mode_changed(self):
        using_default = self.default_radio.isChecked()
        if using_default:
            self.selected_dir = self.default_dir
            self.path_edit.setText(str(self.default_dir))
        self.path_edit.setEnabled(not using_default)
        self._update_status()

    def _browse(self):
        self.custom_radio.setChecked(True)
        folder = QFileDialog.getExistingDirectory(self, "Choose database folder", str(self.selected_dir))
        if folder:
            self.selected_dir = Path(folder)
            self.path_edit.setText(folder)
        self._update_status()

    def _update_status(self):
        candidate = self.selected_dir / app_config.DB_FILE_NAME
        if candidate.exists():
            self.status_label.setText(f"Existing database found here — it will be used ({candidate}).")
        else:
            self.status_label.setText(f"A new, empty database will be created here ({candidate}).")

    def _on_accept(self):
        try:
            self.selected_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.warning(self, "Cannot use this folder", str(exc))
            return
        app_config.set_database_dir(self.selected_dir)
        self.accept()
