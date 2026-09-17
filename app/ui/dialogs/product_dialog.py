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
        self.price_edit = QLineEdit(str(product.price) if product else "0")
        self.reorder_level_edit = QLineEdit(str(product.reorder_level) if product else "0")
        self.opening_stock_edit = QLineEdit("0")

        self.category_combo = QComboBox()
        self.unit_combo = QComboBox()
        self.location_combo = QComboBox()

        with new_session() as session:
            category_id = product.category_id if product else None
            unit_id = product.unit_id if product else None
            location_id = product.location_id if product else None
            self._fill_combo(self.category_combo, self._rows_for_combo(session, Category, category_id))
            self._fill_combo(self.unit_combo, self._rows_for_combo(session, Unit, unit_id))
            self._fill_combo(self.location_combo, self._rows_for_combo(session, Location, location_id))

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
        form.addRow("Price", self.price_edit)
        form.addRow("Reorder level", self.reorder_level_edit)
        if not self.is_edit:
            form.addRow("Opening stock", self.opening_stock_edit)
        form.addRow(buttons)

    @staticmethod
    def _rows_for_combo(session, model, current_id):
        """Active rows, plus the currently-assigned row even if it has since
        been deactivated, so editing an existing product never silently
        drops its category/unit/location."""
        rows = list(list_reference(session, model))
        if current_id is not None and not any(row.id == current_id for row in rows):
            current = session.get(model, current_id)
            if current is not None:
                rows.append(current)
        return rows

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
            price = Decimal(self.price_edit.text() or "0")
            reorder_level = Decimal(self.reorder_level_edit.text() or "0")
            opening_stock = Decimal(self.opening_stock_edit.text() or "0")
        except InvalidOperation:
            QMessageBox.warning(self, "Invalid number", "Price, reorder level and opening stock must be numeric.")
            return
        if price < 0 or reorder_level < 0:
            QMessageBox.warning(self, "Invalid number", "Price and reorder level cannot be negative.")
            return
        if opening_stock < 0:
            QMessageBox.warning(self, "Invalid number", "Opening stock cannot be negative.")
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
            "price": Decimal(self.price_edit.text() or "0"),
            "reorder_level": Decimal(self.reorder_level_edit.text() or "0"),
            "opening_stock": Decimal(self.opening_stock_edit.text() or "0"),
        }
