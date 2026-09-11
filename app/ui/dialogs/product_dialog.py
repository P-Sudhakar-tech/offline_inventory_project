from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
)

from app.data.models import Category, Location, Unit
from app.data.session import new_session
from app.services.master_data import list_reference


class ProductDialog(QDialog):
    def __init__(self, product=None, parent=None):
        super().__init__(parent)
        self.is_edit = product is not None
        self.setWindowTitle("Edit Product" if self.is_edit else "Add Product")

        self.sku_edit = QLineEdit(product.sku if product else "")
        self.barcode_edit = QLineEdit(product.barcode if product and product.barcode else "")
        self.name_edit = QLineEdit(product.name if product else "")
        self.purchase_price_edit = QLineEdit(str(product.purchase_price) if product else "0")
        self.sale_price_edit = QLineEdit(str(product.sale_price) if product else "0")
        self.reorder_level_edit = QLineEdit(str(product.reorder_level) if product else "0")
        self.opening_stock_edit = QLineEdit("0")

        self.category_combo = QComboBox()
        self.unit_combo = QComboBox()
        self.location_combo = QComboBox()

        with new_session() as session:
            self._fill_combo(self.category_combo, list_reference(session, Category))
            self._fill_combo(self.unit_combo, list_reference(session, Unit))
            self._fill_combo(self.location_combo, list_reference(session, Location))

        if product:
            self._select_combo(self.category_combo, product.category_id)
            self._select_combo(self.unit_combo, product.unit_id)
            self._select_combo(self.location_combo, product.location_id)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        form = QFormLayout(self)
        form.addRow("SKU", self.sku_edit)
        form.addRow("Barcode", self.barcode_edit)
        form.addRow("Name", self.name_edit)
        form.addRow("Category", self.category_combo)
        form.addRow("Unit", self.unit_combo)
        form.addRow("Location", self.location_combo)
        form.addRow("Purchase price", self.purchase_price_edit)
        form.addRow("Sale price", self.sale_price_edit)
        form.addRow("Reorder level", self.reorder_level_edit)
        if not self.is_edit:
            form.addRow("Opening stock", self.opening_stock_edit)
        form.addRow(buttons)

    @staticmethod
    def _fill_combo(combo: QComboBox, rows):
        combo.addItem("(none)", None)
        for row in rows:
            combo.addItem(row.name, row.id)

    @staticmethod
    def _select_combo(combo: QComboBox, value_id):
        index = combo.findData(value_id)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def _on_accept(self):
        if not self.sku_edit.text().strip() or not self.name_edit.text().strip():
            QMessageBox.warning(self, "Missing data", "SKU and Name are required.")
            return
        try:
            Decimal(self.purchase_price_edit.text() or "0")
            Decimal(self.sale_price_edit.text() or "0")
            Decimal(self.reorder_level_edit.text() or "0")
            Decimal(self.opening_stock_edit.text() or "0")
        except InvalidOperation:
            QMessageBox.warning(self, "Invalid number", "Prices, reorder level and opening stock must be numeric.")
            return
        self.accept()

    def values(self):
        return {
            "sku": self.sku_edit.text().strip(),
            "barcode": self.barcode_edit.text().strip() or None,
            "name": self.name_edit.text().strip(),
            "category_id": self.category_combo.currentData(),
            "unit_id": self.unit_combo.currentData(),
            "location_id": self.location_combo.currentData(),
            "purchase_price": Decimal(self.purchase_price_edit.text() or "0"),
            "sale_price": Decimal(self.sale_price_edit.text() or "0"),
            "reorder_level": Decimal(self.reorder_level_edit.text() or "0"),
            "opening_stock": Decimal(self.opening_stock_edit.text() or "0"),
        }
