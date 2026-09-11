from datetime import datetime, time

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.data.session import new_session
from app.reports.excel_export import write_table_excel
from app.reports.pdf_export import write_table_pdf
from app.services.reports import (
    current_stock_report,
    low_stock_report,
    out_of_stock_report,
    stock_movement_report,
)

STOCK_HEADERS = ["SKU", "Name", "Stock", "Reorder Level", "Sale Price", "Stock Value"]
MOVEMENT_HEADERS = ["Date", "SKU", "Product", "Reason", "Qty Change", "Balance After", "Reference"]


def _stock_rows(products):
    return [
        [
            p.sku,
            p.name,
            str(p.current_stock),
            str(p.reorder_level),
            str(p.sale_price),
            f"{p.current_stock * p.sale_price:.2f}",
        ]
        for p in products
    ]


class ReportsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        layout.addWidget(self._build_simple_reports_section())
        layout.addWidget(self._build_movement_section())
        layout.addStretch()

    def _build_simple_reports_section(self) -> QWidget:
        section = QWidget()
        grid = QGridLayout(section)
        grid.setSpacing(10)

        specs = [
            ("Current Stock Report", current_stock_report, "current_stock"),
            ("Low Stock Report", low_stock_report, "low_stock"),
            ("Out of Stock Report", out_of_stock_report, "out_of_stock"),
        ]

        for row, (title, fetch_fn, filename) in enumerate(specs):
            grid.addWidget(QLabel(title), row, 0)
            pdf_btn = QPushButton("Export PDF")
            excel_btn = QPushButton("Export Excel")
            pdf_btn.clicked.connect(lambda _, f=fetch_fn, t=title, n=filename: self._export_stock(f, t, n, "pdf"))
            excel_btn.clicked.connect(lambda _, f=fetch_fn, t=title, n=filename: self._export_stock(f, t, n, "xlsx"))
            grid.addWidget(pdf_btn, row, 1)
            grid.addWidget(excel_btn, row, 2)

        return section

    def _build_movement_section(self) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.addWidget(QLabel("Stock Movement Report (by date range)"))

        self.start_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)

        form = QFormLayout()
        form.addRow("Start date", self.start_date)
        form.addRow("End date", self.end_date)
        layout.addLayout(form)

        pdf_btn = QPushButton("Export PDF")
        excel_btn = QPushButton("Export Excel")
        pdf_btn.clicked.connect(lambda: self._export_movement("pdf"))
        excel_btn.clicked.connect(lambda: self._export_movement("xlsx"))

        btn_row = QFormLayout()
        btn_row.addRow(pdf_btn, excel_btn)
        layout.addLayout(btn_row)

        return section

    def _choose_save_path(self, default_name: str, extension: str):
        filter_str = "PDF files (*.pdf)" if extension == "pdf" else "Excel files (*.xlsx)"
        path, _ = QFileDialog.getSaveFileName(self, "Save report", f"{default_name}.{extension}", filter_str)
        return path or None

    def _export_stock(self, fetch_fn, title, filename, extension):
        with new_session() as session:
            products = fetch_fn(session)
        rows = _stock_rows(products)
        path = self._choose_save_path(filename, extension)
        if not path:
            return
        if extension == "pdf":
            write_table_pdf(path, title, STOCK_HEADERS, rows)
        else:
            write_table_excel(path, title, STOCK_HEADERS, rows)
        QMessageBox.information(self, "Report saved", f"Saved to {path}")

    def _export_movement(self, extension):
        start = datetime.combine(self.start_date.date().toPython(), time.min)
        end = datetime.combine(self.end_date.date().toPython(), time.max)
        with new_session() as session:
            pairs = stock_movement_report(session, start, end)

        rows = [
            [
                txn.created_at.strftime("%Y-%m-%d %H:%M"),
                product.sku,
                product.name,
                txn.reason,
                str(txn.qty_delta),
                str(txn.balance_after),
                txn.reference or "",
            ]
            for txn, product in pairs
        ]
        path = self._choose_save_path("stock_movement", extension)
        if not path:
            return
        title = "Stock Movement Report"
        if extension == "pdf":
            write_table_pdf(path, title, MOVEMENT_HEADERS, rows)
        else:
            write_table_excel(path, title, MOVEMENT_HEADERS, rows)
        QMessageBox.information(self, "Report saved", f"Saved to {path}")
