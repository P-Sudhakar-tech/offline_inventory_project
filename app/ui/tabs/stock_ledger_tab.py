from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.data.session import new_session
from app.services.master_data import list_products
from app.services.reports import product_ledger


class StockLedgerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self.refresh)

        form = QFormLayout()
        form.addRow("Product", self.product_combo)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Date", "Reason", "Qty Change", "Balance After"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.addLayout(form)
        layout.addWidget(self.table)

        self.refresh_products()

    def refresh_products(self):
        self.product_combo.blockSignals(True)
        self.product_combo.clear()
        with new_session() as session:
            for product in list_products(session, include_inactive=True):
                self.product_combo.addItem(f"{product.sku} — {product.name}", product.id)
        self.product_combo.blockSignals(False)
        self.refresh()

    def refresh(self):
        product_id = self.product_combo.currentData()
        self.table.setRowCount(0)
        if product_id is None:
            return
        with new_session() as session:
            rows = product_ledger(session, product_id)
            self.table.setRowCount(len(rows))
            for i, txn in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(txn.created_at.strftime("%Y-%m-%d %H:%M")))
                self.table.setItem(i, 1, QTableWidgetItem(txn.reason))
                self.table.setItem(i, 2, QTableWidgetItem(str(txn.qty_delta)))
                self.table.setItem(i, 3, QTableWidgetItem(str(txn.balance_after)))
