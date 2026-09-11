from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.data.session import new_session
from app.security.session_context import get_current_user
from app.services.auth import (
    DuplicateUsernameError,
    change_password,
    change_role,
    create_user,
    list_users,
    set_user_active,
)
from app.ui.dialogs.user_dialog import UserDialog


class UserManagementTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Username", "Role", "Active"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        add_btn = QPushButton("Add User")
        add_btn.setObjectName("PrimaryButton")
        edit_btn = QPushButton("Edit User")
        self.toggle_btn = QPushButton("Deactivate")
        add_btn.clicked.connect(self._add)
        edit_btn.clicked.connect(self._edit)
        self.toggle_btn.clicked.connect(self._toggle_active)

        btn_row = QHBoxLayout()
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(self.toggle_btn)
        btn_row.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.addLayout(btn_row)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        with new_session() as session:
            rows = list_users(session)
            self.table.setRowCount(len(rows))
            self._ids = []
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(row.username))
                self.table.setItem(i, 1, QTableWidgetItem(row.role))
                self.table.setItem(i, 2, QTableWidgetItem("Yes" if row.is_active else "No"))
                self._ids.append((row.id, row.username, row.is_active))

    def _selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._ids):
            return None
        return self._ids[row]

    def _add(self):
        dialog = UserDialog(parent=self)
        if dialog.exec():
            values = dialog.values()
            with new_session() as session:
                try:
                    create_user(session, values["username"], values["password"], values["role"])
                    session.commit()
                except DuplicateUsernameError as exc:
                    QMessageBox.warning(self, "Duplicate username", str(exc))
            self.refresh()

    def _edit(self):
        selected = self._selected()
        if selected is None:
            QMessageBox.information(self, "No selection", "Select a user to edit.")
            return
        user_id, username, _ = selected
        with new_session() as session:
            from app.data.models import User

            user = session.get(User, user_id)
            dialog = UserDialog(user=user, parent=self)
        if dialog.exec():
            values = dialog.values()
            with new_session() as session:
                change_role(session, user_id, values["role"])
                if values["password"]:
                    change_password(session, user_id, values["password"])
                session.commit()
        self.refresh()

    def _toggle_active(self):
        selected = self._selected()
        if selected is None:
            QMessageBox.information(self, "No selection", "Select a user to activate/deactivate.")
            return
        user_id, username, is_active = selected
        current = get_current_user()
        if current is not None and current.id == user_id and is_active:
            QMessageBox.warning(self, "Not allowed", "You cannot deactivate your own account.")
            return
        with new_session() as session:
            set_user_active(session, user_id, not is_active)
            session.commit()
        self.refresh()
