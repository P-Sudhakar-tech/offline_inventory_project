from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.data.session import new_session
from app.services.master_data import list_products
from app.services.stock_ledger import InsufficientStockError
from app.services.transactions import InvalidLineItemError, create_adjustment


class AdjustmentTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("Card")

        self.product_combo = QComboBox()
        self.refresh_products()

        self.delta_edit = QLineEdit()
        self.delta_edit.setPlaceholderText("e.g. -2 for a shortage, 5 for a found item")

        self.reason_edit = QLineEdit()
        self.reason_edit.setPlaceholderText("Reason (required)")

        save_btn = QPushButton("Apply Adjustment")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self._save)

        form = QFormLayout()
        form.addRow("Product", self.product_combo)
        form.addRow("Quantity change", self.delta_edit)
        form.addRow("Reason", self.reason_edit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.addLayout(form)
        layout.addWidget(save_btn)
        layout.addStretch()

    def refresh_products(self):
        current = self.product_combo.currentData()
        self.product_combo.blockSignals(True)
        self.product_combo.clear()
        with new_session() as session:
            for product in list_products(session):
                self.product_combo.addItem(f"{product.sku} — {product.name}", product.id)
        index = self.product_combo.findData(current)
        self.product_combo.setCurrentIndex(index if index >= 0 else 0)
        self.product_combo.blockSignals(False)

    def _save(self):
        product_id = self.product_combo.currentData()
        if product_id is None:
            QMessageBox.information(self, "No product", "Add a product first.")
            return
        try:
            delta = Decimal(self.delta_edit.text())
        except InvalidOperation:
            QMessageBox.warning(self, "Invalid number", "Quantity change must be numeric.")
            return
        if delta == 0:
            QMessageBox.warning(self, "No change", "Quantity change cannot be zero.")
            return
        if not self.reason_edit.text().strip():
            QMessageBox.warning(self, "Reason required", "A reason is required for stock adjustments.")
            return

        try:
            with new_session() as session:
                create_adjustment(session, product_id, delta, self.reason_edit.text())
                session.commit()
        except InsufficientStockError as exc:
            QMessageBox.warning(self, "Insufficient stock", str(exc))
            return
        except InvalidLineItemError as exc:
            QMessageBox.warning(self, "Invalid data", str(exc))
            return

        QMessageBox.information(self, "Saved", "Adjustment applied.")
        self.delta_edit.clear()
        self.reason_edit.clear()
