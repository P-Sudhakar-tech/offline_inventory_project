from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.data.models import Category, Location, Unit
from app.ui.tabs.adjustment_tab import AdjustmentTab
from app.ui.tabs.customer_tab import CustomerTab
from app.ui.tabs.product_tab import ProductTab
from app.ui.tabs.purchase_tab import PurchaseTab
from app.ui.tabs.reference_tab import ReferenceTab
from app.ui.tabs.sale_tab import SaleTab
from app.ui.tabs.supplier_tab import SupplierTab

NAV_ITEMS = [
    "Products",
    "Categories",
    "Units",
    "Locations",
    "Suppliers",
    "Customers",
    "Purchase / Stock In",
    "Stock Out / Sale",
    "Stock Adjustment",
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Offline Inventory Management System")
        self.resize(1200, 760)

        self.product_tab = ProductTab()
        self.pages = [
            self.product_tab,
            ReferenceTab(Category, "Category"),
            ReferenceTab(Unit, "Unit"),
            ReferenceTab(Location, "Location"),
            SupplierTab(),
            CustomerTab(),
            PurchaseTab(),
            SaleTab(),
            AdjustmentTab(),
        ]

        central = QWidget()
        central.setObjectName("ContentArea")
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_content_area(), stretch=1)

        self.setCentralWidget(central)
        self.nav_list.setCurrentRow(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(230)

        brand = QLabel("Inventory Manager")
        brand.setObjectName("BrandLabel")

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("NavList")
        self.nav_list.addItems(NAV_ITEMS)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(brand)
        layout.addWidget(self.nav_list, stretch=1)

        return sidebar

    def _build_content_area(self) -> QWidget:
        content = QWidget()
        content.setObjectName("ContentArea")

        header = QWidget()
        header.setObjectName("HeaderBar")
        self.page_title = QLabel(NAV_ITEMS[0])
        self.page_title.setObjectName("PageTitle")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(self.page_title)

        self.stack = QStackedWidget()
        for page in self.pages:
            self.stack.addWidget(page)

        stack_wrapper = QWidget()
        stack_layout = QVBoxLayout(stack_wrapper)
        stack_layout.setContentsMargins(20, 20, 20, 20)
        stack_layout.addWidget(self.stack)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(header)
        layout.addWidget(stack_wrapper, stretch=1)

        return content

    def _on_nav_changed(self, index: int):
        if index < 0:
            return
        self.stack.setCurrentIndex(index)
        self.page_title.setText(NAV_ITEMS[index])
        if self.stack.widget(index) is self.product_tab:
            self.product_tab.refresh()
