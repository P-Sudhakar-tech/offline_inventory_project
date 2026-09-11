from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.data.models import Category, Location, Unit
from app.ui.style_utils import apply_shadows_to_cards
from app.ui.tabs.adjustment_tab import AdjustmentTab
from app.ui.tabs.audit_log_tab import AuditLogTab
from app.ui.tabs.customer_tab import CustomerTab
from app.ui.tabs.dashboard_tab import DashboardTab
from app.ui.tabs.product_tab import ProductTab
from app.ui.tabs.purchase_tab import PurchaseTab
from app.ui.tabs.reference_tab import ReferenceTab
from app.ui.tabs.reports_tab import ReportsTab
from app.ui.tabs.sale_tab import SaleTab
from app.ui.tabs.settings_tab import SettingsTab
from app.ui.tabs.stock_ledger_tab import StockLedgerTab
from app.ui.tabs.supplier_tab import SupplierTab
from app.ui.tabs.user_management_tab import UserManagementTab

ALL_ROLES = {"admin", "manager", "operator", "viewer"}

# Each entry: (sidebar label with icon, page factory, roles allowed to see it)
NAV_CATALOG = [
    ("📊  Dashboard", DashboardTab, ALL_ROLES),
    ("📦  Products", ProductTab, {"admin", "manager", "operator"}),
    ("🏷️  Categories", lambda: ReferenceTab(Category, "Category"), {"admin", "manager"}),
    ("📐  Units", lambda: ReferenceTab(Unit, "Unit"), {"admin", "manager"}),
    ("📍  Locations", lambda: ReferenceTab(Location, "Location"), {"admin", "manager"}),
    ("🚚  Suppliers", SupplierTab, {"admin", "manager"}),
    ("🧑‍🤝‍🧑  Customers", CustomerTab, {"admin", "manager"}),
    ("🛒  Purchase / Stock In", PurchaseTab, {"admin", "manager", "operator"}),
    ("💵  Stock Out / Sale", SaleTab, {"admin", "manager", "operator"}),
    ("🛠️  Stock Adjustment", AdjustmentTab, {"admin", "manager", "operator"}),
    ("📒  Stock Ledger", StockLedgerTab, ALL_ROLES),
    ("📈  Reports", ReportsTab, ALL_ROLES),
    ("👤  Users", UserManagementTab, {"admin"}),
    ("🕵️  Audit Log", AuditLogTab, {"admin"}),
    ("⚙️  Application Settings", SettingsTab, {"admin"}),
]


class MainWindow(QMainWindow):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.logout_requested = False
        self.setWindowTitle("Offline Inventory Management System")
        self.resize(1240, 780)

        self.nav_labels = []
        self.pages = []
        for label, factory, roles in NAV_CATALOG:
            if current_user.role in roles:
                self.nav_labels.append(label)
                self.pages.append(factory())

        central = QWidget()
        central.setObjectName("ContentArea")
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_content_area(), stretch=1)

        self.setCentralWidget(central)
        self.nav_list.setCurrentRow(0)
        apply_shadows_to_cards(self)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(250)

        brand = QLabel("Inventory Manager")
        brand.setObjectName("BrandLabel")

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("NavList")
        self.nav_list.addItems(self.nav_labels)
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
        self.page_title = QLabel(self.nav_labels[0])
        self.page_title.setObjectName("PageTitle")

        user_badge = QLabel(f"{self.current_user.username} · {self.current_user.role.title()}")
        user_badge.setObjectName("UserBadge")

        logout_btn = QPushButton("Log Out")
        logout_btn.setObjectName("GhostButton")
        logout_btn.clicked.connect(self._logout)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        header_layout.addWidget(self.page_title)
        header_layout.addStretch()
        header_layout.addWidget(user_badge)
        header_layout.addWidget(logout_btn)

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
        self.page_title.setText(self.nav_labels[index])

        page = self.stack.widget(index)
        if hasattr(page, "refresh_products"):
            page.refresh_products()
        elif hasattr(page, "refresh"):
            page.refresh()

    def _logout(self):
        self.logout_requested = True
        self.close()
