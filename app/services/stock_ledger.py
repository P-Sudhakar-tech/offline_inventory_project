from decimal import Decimal

from sqlalchemy.orm import Session

from app.data.models.product import Product
from app.data.models.stock_transaction import StockTransaction


class InsufficientStockError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


def record_movement(
    session: Session,
    product_id: int,
    qty_delta: Decimal,
    reason: str,
    reference: str | None = None,
    allow_negative: bool = False,
) -> StockTransaction:
    """Apply a stock movement and append it to the immutable ledger.

    This is the single path by which Product.current_stock may change.
    Runs inside the caller's transaction: the product row is locked for
    update (via SELECT ... within the session's transaction) so concurrent
    movements against the same product serialize instead of racing.
    """
    product = session.get(Product, product_id, with_for_update=True)
    if product is None:
        raise ProductNotFoundError(f"Product {product_id} does not exist")

    new_balance = product.current_stock + qty_delta
    if new_balance < 0 and not allow_negative:
        raise InsufficientStockError(
            f"Movement would take product {product_id} stock to {new_balance}"
        )

    product.current_stock = new_balance

    txn = StockTransaction(
        product_id=product_id,
        qty_delta=qty_delta,
        balance_after=new_balance,
        reason=reason,
        reference=reference,
    )
    session.add(txn)
    session.flush()
    return txn
