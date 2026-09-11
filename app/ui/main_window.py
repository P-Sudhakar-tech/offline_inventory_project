from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.data.models import Category, Location, Unit
from app.ui.tabs.adjustment_tab import AdjustmentTab
from app.ui.tabs.customer_tab import CustomerTab
from app.ui.tabs.product_tab import ProductTab
from app.ui.tabs.purchase_tab import PurchaseTab
from app.ui.tabs.reference_tab import ReferenceTab
from app.ui.tabs.sale_tab import SaleTab
from app.ui.tabs.supplier_tab import SupplierTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Offline Inventory Management System")
        self.resize(1024, 700)

        self.tabs = QTabWidget()
        self.product_tab = ProductTab()
        self.tabs.addTab(self.product_tab, "Products")
        self.tabs.addTab(ReferenceTab(Category, "Category"), "Categories")
        self.tabs.addTab(ReferenceTab(Unit, "Unit"), "Units")
        self.tabs.addTab(ReferenceTab(Location, "Location"), "Locations")
        self.tabs.addTab(SupplierTab(), "Suppliers")
        self.tabs.addTab(CustomerTab(), "Customers")
        self.tabs.addTab(PurchaseTab(), "Purchase / Stock In")
        self.tabs.addTab(SaleTab(), "Stock Out / Sale")
        self.tabs.addTab(AdjustmentTab(), "Stock Adjustment")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tabs)

    def _on_tab_changed(self, index):
        if self.tabs.widget(index) is self.product_tab:
            self.product_tab.refresh()
