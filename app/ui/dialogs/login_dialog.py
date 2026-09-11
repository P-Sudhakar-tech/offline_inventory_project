from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from app.data.session import new_session
from app.services.auth import InvalidCredentialsError, authenticate


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign In")
        self.setMinimumWidth(340)
        self.authenticated_user = None

        title = QLabel("Offline Inventory Management")
        title.setObjectName("PageTitle")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignCenter)

        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.returnPressed.connect(self._on_accept)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #dc2626;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        form = QFormLayout()
        form.addRow("Username", self.username_edit)
        form.addRow("Password", self.password_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Ok).setText("Sign In")
        buttons.button(QDialogButtonBox.Ok).setObjectName("PrimaryButton")
        buttons.accepted.connect(self._on_accept)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)

    def _on_accept(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        if not username or not password:
            self._show_error("Enter both a username and a password.")
            return

        with new_session() as session:
            try:
                user = authenticate(session, username, password)
            except InvalidCredentialsError as exc:
                self._show_error(str(exc))
                return
            session.refresh(user)
            self.authenticated_user = user

        self.accept()

    def _show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.show()
        self.password_edit.clear()
        self.password_edit.setFocus()
