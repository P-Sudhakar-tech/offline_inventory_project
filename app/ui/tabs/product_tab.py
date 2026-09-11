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
    DuplicateSkuError,
    create_product,
    list_products,
    set_product_active,
    update_product,
)
from app.ui.dialogs.product_dialog import ProductDialog

COLUMNS = ["SKU", "Name", "Purchase Price", "Sale Price", "Stock", "Reorder Level", "Active"]


class ProductTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.show_inactive = QCheckBox("Show inactive products")
        self.show_inactive.stateChanged.connect(self.refresh)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        add_btn = QPushButton("Add")
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
        layout.addLayout(btn_row)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        with new_session() as session:
            rows = list_products(session, include_inactive=self.show_inactive.isChecked())
            self.table.setRowCount(len(rows))
            self._ids = []
            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(row.sku))
                self.table.setItem(i, 1, QTableWidgetItem(row.name))
                self.table.setItem(i, 2, QTableWidgetItem(str(row.purchase_price)))
                self.table.setItem(i, 3, QTableWidgetItem(str(row.sale_price)))
                self.table.setItem(i, 4, QTableWidgetItem(str(row.current_stock)))
                self.table.setItem(i, 5, QTableWidgetItem(str(row.reorder_level)))
                self.table.setItem(i, 6, QTableWidgetItem("Yes" if row.is_active else "No"))
                self._ids.append((row.id, row.is_active))

    def _selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._ids):
            return None
        return self._ids[row]

    def _add(self):
        dialog = ProductDialog(parent=self)
        if dialog.exec():
            values = dialog.values()
            with new_session() as session:
                try:
                    create_product(session, **values)
                    session.commit()
                except DuplicateSkuError as exc:
                    QMessageBox.warning(self, "Duplicate SKU", str(exc))
            self.refresh()

    def _edit(self):
        selected = self._selected()
        if selected is None:
            QMessageBox.information(self, "No selection", "Select a product to edit.")
            return
        product_id, _ = selected
        with new_session() as session:
            from app.data.models import Product

            product = session.get(Product, product_id)
            dialog = ProductDialog(product=product, parent=self)
        if dialog.exec():
            values = dialog.values()
            values.pop("opening_stock", None)
            with new_session() as session:
                try:
                    update_product(session, product_id, **values)
                    session.commit()
                except DuplicateSkuError as exc:
                    QMessageBox.warning(self, "Duplicate SKU", str(exc))
        self.refresh()

    def _toggle_active(self):
        selected = self._selected()
        if selected is None:
            QMessageBox.information(self, "No selection", "Select a product to activate/deactivate.")
            return
        product_id, is_active = selected
        with new_session() as session:
            set_product_active(session, product_id, not is_active)
            session.commit()
        self.refresh()
