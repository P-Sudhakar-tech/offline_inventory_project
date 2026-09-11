from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import IntegrityError

from app.data.session import new_session
from app.services.master_data import delete_supplier, list_suppliers, save_supplier
from app.ui.dialogs.supplier_dialog import SupplierDialog


class SupplierTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("Card")

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Contact", "Address"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        add_btn = QPushButton("Add")
        add_btn.setObjectName("PrimaryButton")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")
        add_btn.clicked.connect(self._add)
        edit_btn.clicked.connect(self._edit)
        delete_btn.clicked.connect(self._delete)

        btn_row = QHBoxLayout()
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.addLayout(btn_row)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        with new_session() as session:
            rows = list_suppliers(session)
            self.table.setRowCount(len(rows))
            self._ids = []
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(row.name))
                self.table.setItem(i, 1, QTableWidgetItem(row.contact or ""))
                self.table.setItem(i, 2, QTableWidgetItem(row.address or ""))
                self._ids.append(row.id)

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._ids):
            return None
        return self._ids[row]

    def _add(self):
        dialog = SupplierDialog(parent=self)
        if dialog.exec():
            name, contact, address = dialog.values()
            with new_session() as session:
                save_supplier(session, None, name, contact, address)
                session.commit()
            self.refresh()

    def _edit(self):
        row_id = self._selected_id()
        if row_id is None:
            QMessageBox.information(self, "No selection", "Select a supplier to edit.")
            return
        row = self.table.currentRow()
        dialog = SupplierDialog(
            self.table.item(row, 0).text(),
            self.table.item(row, 1).text(),
            self.table.item(row, 2).text(),
            parent=self,
        )
        if dialog.exec():
            name, contact, address = dialog.values()
            with new_session() as session:
                save_supplier(session, row_id, name, contact, address)
                session.commit()
            self.refresh()

    def _delete(self):
        row_id = self._selected_id()
        if row_id is None:
            QMessageBox.information(self, "No selection", "Select a supplier to delete.")
            return
        if QMessageBox.question(self, "Confirm delete", "Delete this supplier?") == QMessageBox.Yes:
            with new_session() as session:
                try:
                    delete_supplier(session, row_id)
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    QMessageBox.warning(self, "Cannot delete", "This supplier is used by purchase records.")
            self.refresh()
