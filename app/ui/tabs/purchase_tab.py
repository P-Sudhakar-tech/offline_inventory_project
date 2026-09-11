from app.data.models import Supplier
from app.services.master_data import list_suppliers
from app.services.transactions import LineItem, create_purchase
from app.ui.tabs.transaction_tab_base import TransactionTabBase


class PurchaseTab(TransactionTabBase):
    party_label = "Supplier"
    price_field = "purchase_price"

    def __init__(self, parent=None):
        super().__init__(Supplier, list_suppliers, parent)

    def perform_save(self, session, party_id, reference, items):
        line_items = [LineItem(product.id, qty, price) for product, qty, price in items]
        return create_purchase(session, supplier_id=party_id, reference=reference, items=line_items)
