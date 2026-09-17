from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.data.session import new_session
from app.services.master_data import list_customers, save_customer, set_customer_active
from app.ui.dialogs.customer_dialog import CustomerDialog


class CustomerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("Card")

        self.show_inactive = QCheckBox("Show inactive customers")
        self.show_inactive.stateChanged.connect(self.refresh)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Contact", "Active"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        add_btn = QPushButton("Add")
        add_btn.setObjectName("PrimaryButton")
        edit_btn = QPushButton("Edit")
        self.toggle_btn = QPushButton("Deactivate")
        add_btn.clicked.connect(self._add)
        edit_btn.clicked.connect(self._edit)
        self.toggle_btn.clicked.connect(self._toggle_active)

        btn_row = QHBoxLayout()
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(self.toggle_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.show_inactive)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.addLayout(btn_row)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        with new_session() as session:
            rows = list_customers(session, include_inactive=self.show_inactive.isChecked())
            self.table.setRowCount(len(rows))
            self._ids = []
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(row.name))
                self.table.setItem(i, 1, QTableWidgetItem(row.contact or ""))
                self.table.setItem(i, 2, QTableWidgetItem("Yes" if row.is_active else "No"))
                self._ids.append((row.id, row.is_active))

    def _selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._ids):
            return None
        return self._ids[row]

    def _selected_id(self):
        selected = self._selected()
        return selected[0] if selected else None

    def _add(self):
        dialog = CustomerDialog(parent=self)
        if dialog.exec():
            name, contact = dialog.values()
            with new_session() as session:
                save_customer(session, None, name, contact)
                session.commit()
            self.refresh()

    def _edit(self):
        row_id = self._selected_id()
        if row_id is None:
            QMessageBox.information(self, "No selection", "Select a customer to edit.")
            return
        row = self.table.currentRow()
        dialog = CustomerDialog(
            self.table.item(row, 0).text(),
            self.table.item(row, 1).text(),
            parent=self,
        )
        if dialog.exec():
            name, contact = dialog.values()
            with new_session() as session:
                save_customer(session, row_id, name, contact)
                session.commit()
            self.refresh()

    def _toggle_active(self):
        selected = self._selected()
        if selected is None:
            QMessageBox.information(self, "No selection", "Select a customer to activate/deactivate.")
            return
        row_id, is_active = selected
        with new_session() as session:
            set_customer_active(session, row_id, not is_active)
            session.commit()
        self.refresh()
