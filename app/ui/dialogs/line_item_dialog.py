from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
)

from app.data.session import new_session
from app.services.master_data import list_products


class LineItemDialog(QDialog):
    """Pick a product and enter quantity/unit price for one purchase/sale line."""

    def __init__(self, default_price_field: str = "purchase_price", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Line Item")
        self._default_price_field = default_price_field

        self.product_combo = QComboBox()
        with new_session() as session:
            self._products = {p.id: p for p in list_products(session)}
        for product in self._products.values():
            self.product_combo.addItem(f"{product.sku} — {product.name}", product.id)
        self.product_combo.currentIndexChanged.connect(self._prefill_price)

        self.quantity_edit = QLineEdit("1")
        self.price_edit = QLineEdit("0")

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        form = QFormLayout(self)
        form.addRow("Product", self.product_combo)
        form.addRow("Quantity", self.quantity_edit)
        form.addRow("Unit price", self.price_edit)
        form.addRow(buttons)

        self._prefill_price()

    def _prefill_price(self):
        product_id = self.product_combo.currentData()
        product = self._products.get(product_id)
        if product is not None:
            price = getattr(product, self._default_price_field)
            self.price_edit.setText(str(price))

    def _on_accept(self):
        if self.product_combo.currentData() is None:
            QMessageBox.warning(self, "No product", "Add a product first, or select one.")
            return
        try:
            qty = Decimal(self.quantity_edit.text())
            price = Decimal(self.price_edit.text())
        except InvalidOperation:
            QMessageBox.warning(self, "Invalid number", "Quantity and price must be numeric.")
            return
        if qty <= 0:
            QMessageBox.warning(self, "Invalid quantity", "Quantity must be greater than zero.")
            return
        if price < 0:
            QMessageBox.warning(self, "Invalid price", "Price cannot be negative.")
            return
        self.accept()

    def values(self):
        product = self._products[self.product_combo.currentData()]
        return product, Decimal(self.quantity_edit.text()), Decimal(self.price_edit.text())
