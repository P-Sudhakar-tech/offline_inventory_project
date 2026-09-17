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
from app.services.master_data import (
    DuplicateNameError,
    create_reference,
    list_reference,
    rename_reference,
    set_reference_active,
)
from app.ui.dialogs.simple_master_dialog import SimpleMasterDialog


class ReferenceTab(QWidget):
    """Reusable list/add/rename/deactivate screen for name-only reference data."""

    def __init__(self, model, title: str, parent=None):
        super().__init__(parent)
        self.model = model
        self.title = title

        self.setObjectName("Card")

        self.show_inactive = QCheckBox(f"Show inactive {self.title.lower()}s")
        self.show_inactive.stateChanged.connect(self.refresh)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Name", "Active"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        add_btn = QPushButton("Add")
        add_btn.setObjectName("PrimaryButton")
        rename_btn = QPushButton("Rename")
        self.toggle_btn = QPushButton("Deactivate")
        add_btn.clicked.connect(self._add)
        rename_btn.clicked.connect(self._rename)
        self.toggle_btn.clicked.connect(self._toggle_active)

        btn_row = QHBoxLayout()
        btn_row.addWidget(add_btn)
        btn_row.addWidget(rename_btn)
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
            rows = list_reference(session, self.model, include_inactive=self.show_inactive.isChecked())
            self.table.setRowCount(len(rows))
            self._ids = []
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(row.name))
                self.table.setItem(i, 1, QTableWidgetItem("Yes" if row.is_active else "No"))
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

    def _toggle_active(self):
        selected = self._selected()
        if selected is None:
            QMessageBox.information(self, "No selection", f"Select a {self.title.lower()} to activate/deactivate.")
            return
        row_id, is_active = selected
        with new_session() as session:
            set_reference_active(session, self.model, row_id, not is_active)
            session.commit()
        self.refresh()
