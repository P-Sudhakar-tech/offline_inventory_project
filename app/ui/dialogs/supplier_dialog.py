from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
)


class SupplierDialog(QDialog):
    def __init__(self, name: str = "", contact: str = "", address: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Supplier")

        self.name_edit = QLineEdit(name)
        self.contact_edit = QLineEdit(contact)
        self.address_edit = QLineEdit(address)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        form = QFormLayout(self)
        form.addRow("Name", self.name_edit)
        form.addRow("Contact", self.contact_edit)
        form.addRow("Address", self.address_edit)
        form.addRow(buttons)

    def _on_accept(self):
        if self.name_edit.text().strip():
            self.accept()

    def values(self):
        return self.name_edit.text(), self.contact_edit.text(), self.address_edit.text()
