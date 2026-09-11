from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.data.session import new_session
from app.services.reports import dashboard_summary, recent_transactions
from app.ui.widgets.kpi_card import KpiCard


class DashboardTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        self.product_count_card = KpiCard("Active Products")
        self.stock_value_card = KpiCard("Total Stock Value")
        self.low_stock_card = KpiCard("Low Stock Items", value_object_name="KpiValueWarning")
        self.out_of_stock_card = KpiCard("Out of Stock Items", value_object_name="KpiValueDanger")

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)
        for card in (
            self.product_count_card,
            self.stock_value_card,
            self.low_stock_card,
            self.out_of_stock_card,
        ):
            kpi_row.addWidget(card)

        section_title = QLabel("Recent Stock Movements")
        section_title.setObjectName("SectionTitle")

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)

        header_row = QHBoxLayout()
        header_row.addWidget(section_title)
        header_row.addStretch()
        header_row.addWidget(refresh_btn)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Date", "Product", "Reason", "Qty Change", "Balance After"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)
        layout.addLayout(kpi_row)
        layout.addLayout(header_row)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        with new_session() as session:
            summary = dashboard_summary(session)
            self.product_count_card.set_value(str(summary.product_count))
            self.stock_value_card.set_value(f"{summary.total_stock_value:,.2f}")
            self.low_stock_card.set_value(str(summary.low_stock_count))
            self.out_of_stock_card.set_value(str(summary.out_of_stock_count))

            rows = recent_transactions(session, limit=15)
            self.table.setRowCount(len(rows))
            for i, (txn, product) in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(txn.created_at.strftime("%Y-%m-%d %H:%M")))
                self.table.setItem(i, 1, QTableWidgetItem(f"{product.sku} — {product.name}"))
                self.table.setItem(i, 2, QTableWidgetItem(txn.reason))
                self.table.setItem(i, 3, QTableWidgetItem(str(txn.qty_delta)))
                self.table.setItem(i, 4, QTableWidgetItem(str(txn.balance_after)))
