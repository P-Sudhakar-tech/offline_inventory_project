from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.data.session import new_session
from app.services.audit import recent_audit_log


class AuditLogTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(refresh_btn)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Date", "User", "Action", "Details"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.addLayout(btn_row)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        with new_session() as session:
            rows = recent_audit_log(session, limit=200)
            self.table.setRowCount(len(rows))
            for i, (log, user) in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(log.created_at.strftime("%Y-%m-%d %H:%M:%S")))
                self.table.setItem(i, 1, QTableWidgetItem(user.username if user else "(system)"))
                self.table.setItem(i, 2, QTableWidgetItem(log.action))
                self.table.setItem(i, 3, QTableWidgetItem(log.details or ""))
