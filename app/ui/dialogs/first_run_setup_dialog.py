from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.data.session import new_session
from app.services.auth import create_user


class FirstRunSetupDialog(QDialog):
    """Shown once, when the local database has no users yet: creates the
    initial administrator account so the app can never be left unusable.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Initial Setup")
        self.setMinimumWidth(360)
        self.created_user = None

        title = QLabel("Create the administrator account")
        title.setObjectName("PageTitle")
        title.setWordWrap(True)

        subtitle = QLabel("This is a one-time step for a new, empty inventory database.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #64748b;")

        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)

        form = QFormLayout()
        form.addRow("Username", self.username_edit)
        form.addRow("Password", self.password_edit)
        form.addRow("Confirm password", self.confirm_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Ok).setText("Create Administrator")
        buttons.button(QDialogButtonBox.Ok).setObjectName("PrimaryButton")
        buttons.accepted.connect(self._on_accept)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_accept(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "Missing data", "Username and password are required.")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "Weak password", "Password must be at least 6 characters.")
            return
        if password != confirm:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return

        with new_session() as session:
            self.created_user = create_user(session, username, password, role="admin")
            session.commit()
            session.refresh(self.created_user)

        self.accept()
