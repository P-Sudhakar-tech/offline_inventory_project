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
from app.services.master_data import (
    DuplicateNameError,
    create_reference,
    delete_reference,
    list_reference,
    rename_reference,
)
from app.ui.dialogs.simple_master_dialog import SimpleMasterDialog


class ReferenceTab(QWidget):
    """Reusable list/add/rename/delete screen for name-only reference data."""

    def __init__(self, model, title: str, parent=None):
        super().__init__(parent)
        self.model = model
        self.title = title

        self.table = QTableWidget(0, 1)
        self.table.setHorizontalHeaderLabels(["Name"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        add_btn = QPushButton("Add")
        rename_btn = QPushButton("Rename")
        delete_btn = QPushButton("Delete")
        add_btn.clicked.connect(self._add)
        rename_btn.clicked.connect(self._rename)
        delete_btn.clicked.connect(self._delete)

        btn_row = QHBoxLayout()
        btn_row.addWidget(add_btn)
        btn_row.addWidget(rename_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(btn_row)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        with new_session() as session:
            rows = list_reference(session, self.model)
            self.table.setRowCount(len(rows))
            self._ids = []
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(row.name))
                self._ids.append(row.id)

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._ids):
            return None
        return self._ids[row]

    def _add(self):
        dialog = SimpleMasterDialog(f"Add {self.title}", parent=self)
        if dialog.exec():
            with new_session() as session:
                try:
                    create_reference(session, self.model, dialog.value())
                    session.commit()
                except DuplicateNameError as exc:
                    QMessageBox.warning(self, "Duplicate", str(exc))
            self.refresh()

    def _rename(self):
        row_id = self._selected_id()
        if row_id is None:
            QMessageBox.information(self, "No selection", "Select a row to rename.")
            return
        current_name = self.table.item(self.table.currentRow(), 0).text()
        dialog = SimpleMasterDialog(f"Rename {self.title}", current_name, parent=self)
        if dialog.exec():
            with new_session() as session:
                try:
                    rename_reference(session, self.model, row_id, dialog.value())
                    session.commit()
                except DuplicateNameError as exc:
                    QMessageBox.warning(self, "Duplicate", str(exc))
            self.refresh()

    def _delete(self):
        row_id = self._selected_id()
        if row_id is None:
            QMessageBox.information(self, "No selection", "Select a row to delete.")
            return
        confirm = QMessageBox.question(
            self, "Confirm delete", f"Delete this {self.title.lower()}?"
        )
        if confirm == QMessageBox.Yes:
            with new_session() as session:
                try:
                    delete_reference(session, self.model, row_id)
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    QMessageBox.warning(
                        self,
                        "Cannot delete",
                        f"This {self.title.lower()} is used by one or more products.",
                    )
            self.refresh()
