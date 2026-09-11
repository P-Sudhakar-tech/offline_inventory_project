from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLineEdit, QVBoxLayout


class SimpleMasterDialog(QDialog):
    """Add/rename dialog for name-only reference data (Category, Unit, Location)."""

    def __init__(self, title: str, initial_name: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)

        self.name_edit = QLineEdit(initial_name)
        self.name_edit.setPlaceholderText("Name")

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.name_edit)
        layout.addWidget(buttons)

    def _on_accept(self):
        if self.name_edit.text().strip():
            self.accept()

    def value(self) -> str:
        return self.name_edit.text().strip()
