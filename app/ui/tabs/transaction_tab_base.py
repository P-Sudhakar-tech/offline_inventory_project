from decimal import Decimal

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.data.session import new_session
from app.services.stock_ledger import InsufficientStockError, ProductNotFoundError
from app.ui.dialogs.line_item_dialog import LineItemDialog


class TransactionTabBase(QWidget):
    """Shared layout for Purchase and Sale screens: party combo, reference,
    a running list of line items, and a Save action that commits everything
    (header + items + ledger movements) as one unit.
    """

    party_label = "Party"
    price_field = "purchase_price"

    def __init__(self, party_model, list_parties_fn, parent=None):
        super().__init__(parent)
        self._party_model = party_model
        self._list_parties_fn = list_parties_fn
        self._items = []  # list[(product, qty, price)]

        self.setObjectName("Card")

        self.party_combo = QComboBox()
        self.reference_edit = QLineEdit()
        with new_session() as session:
            self.party_combo.addItem("(none)", None)
            for row in self._list_parties_fn(session):
                self.party_combo.addItem(row.name, row.id)

        form = QFormLayout()
        form.addRow(self.party_label, self.party_combo)
        form.addRow("Reference", self.reference_edit)

        add_line_btn = QPushButton("Add Line Item")
        remove_line_btn = QPushButton("Remove Selected Line")
        save_btn = QPushButton("Save")
        save_btn.setObjectName("PrimaryButton")
        add_line_btn.clicked.connect(self._add_line)
        remove_line_btn.clicked.connect(self._remove_line)
        save_btn.clicked.connect(self._save)

        btn_row = QHBoxLayout()
        btn_row.addWidget(add_line_btn)
        btn_row.addWidget(remove_line_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["SKU", "Name", "Quantity", "Unit Price"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.addLayout(form)
        layout.addLayout(btn_row)
        layout.addWidget(self.table)

    def _add_line(self):
        dialog = LineItemDialog(default_price_field=self.price_field, parent=self)
        if dialog.exec():
            product, qty, price = dialog.values()
            self._items.append((product, qty, price))
            self._refresh_table()

    def _remove_line(self):
        row = self.table.currentRow()
        if row < 0:
            return
        del self._items[row]
        self._refresh_table()

    def _refresh_table(self):
        self.table.setRowCount(len(self._items))
        for i, (product, qty, price) in enumerate(self._items):
            self.table.setItem(i, 0, QTableWidgetItem(product.sku))
            self.table.setItem(i, 1, QTableWidgetItem(product.name))
            self.table.setItem(i, 2, QTableWidgetItem(str(qty)))
            self.table.setItem(i, 3, QTableWidgetItem(str(price)))

    def _reset_form(self):
        self._items = []
        self._refresh_table()
        self.reference_edit.clear()
        self.party_combo.setCurrentIndex(0)

    def refresh_products(self):
        """Reload the party list; called whenever this screen regains focus
        so suppliers/customers added elsewhere show up without a restart."""
        current = self.party_combo.currentData()
        self.party_combo.blockSignals(True)
        self.party_combo.clear()
        self.party_combo.addItem("(none)", None)
        with new_session() as session:
            for row in self._list_parties_fn(session):
                self.party_combo.addItem(row.name, row.id)
        index = self.party_combo.findData(current)
        self.party_combo.setCurrentIndex(index if index >= 0 else 0)
        self.party_combo.blockSignals(False)

    def _save(self):
        if not self._items:
            QMessageBox.information(self, "No items", "Add at least one line item first.")
            return
        party_id = self.party_combo.currentData()
        reference = self.reference_edit.text().strip() or None
        try:
            with new_session() as session:
                self.perform_save(session, party_id, reference, self._items)
                session.commit()
        except InsufficientStockError as exc:
            QMessageBox.warning(self, "Insufficient stock", str(exc))
            return
        except ProductNotFoundError as exc:
            QMessageBox.warning(self, "Product not found", str(exc))
            return
        QMessageBox.information(self, "Saved", "Transaction saved.")
        self._reset_form()

    def perform_save(self, session, party_id, reference, items):
        raise NotImplementedError
