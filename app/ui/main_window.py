from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.data.models import Category, Location, Unit
from app.ui.tabs.customer_tab import CustomerTab
from app.ui.tabs.product_tab import ProductTab
from app.ui.tabs.reference_tab import ReferenceTab
from app.ui.tabs.supplier_tab import SupplierTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Offline Inventory Management System")
        self.resize(1024, 700)

        tabs = QTabWidget()
        tabs.addTab(ProductTab(), "Products")
        tabs.addTab(ReferenceTab(Category, "Category"), "Categories")
        tabs.addTab(ReferenceTab(Unit, "Unit"), "Units")
        tabs.addTab(ReferenceTab(Location, "Location"), "Locations")
        tabs.addTab(SupplierTab(), "Suppliers")
        tabs.addTab(CustomerTab(), "Customers")

        self.setCentralWidget(tabs)
