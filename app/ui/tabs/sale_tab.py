from app.data.models import Customer
from app.services.master_data import list_customers
from app.services.transactions import LineItem, create_sale
from app.ui.tabs.transaction_tab_base import TransactionTabBase


class SaleTab(TransactionTabBase):
    party_label = "Customer"
    price_field = "sale_price"

    def __init__(self, parent=None):
        super().__init__(Customer, list_customers, parent)

    def perform_save(self, session, party_id, reference, items):
        line_items = [LineItem(product.id, qty, price) for product, qty, price in items]
        return create_sale(session, customer_id=party_id, reference=reference, items=line_items)
