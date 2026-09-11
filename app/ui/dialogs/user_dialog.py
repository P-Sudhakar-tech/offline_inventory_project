from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
)

from app.data.models import ROLES


class UserDialog(QDialog):
    """Add mode (user=None): username/password/role, all required.
    Edit mode (user given): username fixed, role editable, password fields
    optional — leave blank to keep the existing password.
    """

    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.is_edit = user is not None
        self.setWindowTitle("Edit User" if self.is_edit else "Add User")

        self.username_edit = QLineEdit(user.username if user else "")
        self.username_edit.setEnabled(not self.is_edit)

        self.role_combo = QComboBox()
        self.role_combo.addItems(ROLES)
        if user:
            self.role_combo.setCurrentText(user.role)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Leave blank to keep current password" if self.is_edit else "")

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        form = QFormLayout(self)
        form.addRow("Username", self.username_edit)
        form.addRow("Role", self.role_combo)
        form.addRow("Password", self.password_edit)
        form.addRow("Confirm password", self.confirm_edit)
        form.addRow(buttons)

    def _on_accept(self):
        if not self.username_edit.text().strip():
            QMessageBox.warning(self, "Missing data", "Username is required.")
            return

        password = self.password_edit.text()
        if not self.is_edit and not password:
            QMessageBox.warning(self, "Missing data", "Password is required for a new user.")
            return
        if password and len(password) < 6:
            QMessageBox.warning(self, "Weak password", "Password must be at least 6 characters.")
            return
        if password != self.confirm_edit.text():
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return

        self.accept()

    def values(self):
        return {
            "username": self.username_edit.text().strip(),
            "role": self.role_combo.currentText(),
            "password": self.password_edit.text() or None,
        }
