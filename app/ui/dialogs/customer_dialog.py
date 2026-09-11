from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
)


class CustomerDialog(QDialog):
    def __init__(self, name: str = "", contact: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customer")

        self.name_edit = QLineEdit(name)
        self.contact_edit = QLineEdit(contact)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        form = QFormLayout(self)
        form.addRow("Name", self.name_edit)
        form.addRow("Contact", self.contact_edit)
        form.addRow(buttons)

    def _on_accept(self):
        if self.name_edit.text().strip():
            self.accept()

    def values(self):
        return self.name_edit.text(), self.contact_edit.text()
