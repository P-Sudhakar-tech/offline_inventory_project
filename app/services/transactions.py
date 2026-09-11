from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.data.models import Purchase, PurchaseItem, Sale, SaleItem, StockAdjustment
from app.services.audit import log_action
from app.services.stock_ledger import record_movement


@dataclass
class LineItem:
    product_id: int
    quantity: Decimal
    unit_price: Decimal


class EmptyTransactionError(Exception):
    pass


class InvalidLineItemError(Exception):
    pass


def _validate_line_items(items: list[LineItem]) -> None:
    for item in items:
        if item.quantity <= 0:
            raise InvalidLineItemError(f"Line item quantity must be greater than zero (got {item.quantity})")
        if item.unit_price < 0:
            raise InvalidLineItemError(f"Line item price cannot be negative (got {item.unit_price})")


def create_purchase(
    session: Session,
    supplier_id: int | None,
    reference: str | None,
    items: list[LineItem],
) -> Purchase:
    if not items:
        raise EmptyTransactionError("A purchase needs at least one line item")
    _validate_line_items(items)

    purchase = Purchase(supplier_id=supplier_id, reference=reference)
    session.add(purchase)
    session.flush()

    for item in items:
        session.add(
            PurchaseItem(
                purchase_id=purchase.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
        )
        record_movement(
            session,
            item.product_id,
            item.quantity,
            reason="purchase",
            reference=reference or f"purchase#{purchase.id}",
        )

    session.flush()
    return purchase


def create_sale(
    session: Session,
    customer_id: int | None,
    reference: str | None,
    items: list[LineItem],
) -> Sale:
    if not items:
        raise EmptyTransactionError("A sale needs at least one line item")
    _validate_line_items(items)

    sale = Sale(customer_id=customer_id, reference=reference)
    session.add(sale)
    session.flush()

    for item in items:
        session.add(
            SaleItem(
                sale_id=sale.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
        )
        record_movement(
            session,
            item.product_id,
            -item.quantity,
            reason="sale",
            reference=reference or f"sale#{sale.id}",
        )

    session.flush()
    return sale


def create_adjustment(
    session: Session,
    product_id: int,
    quantity_delta: Decimal,
    reason: str,
) -> StockAdjustment:
    reason = reason.strip()
    if not reason:
        raise ValueError("Stock adjustment requires a reason")
    if quantity_delta == 0:
        raise InvalidLineItemError("Adjustment quantity change cannot be zero")

    adjustment = StockAdjustment(
        product_id=product_id,
        quantity_delta=quantity_delta,
        reason=reason,
    )
    session.add(adjustment)
    session.flush()

    record_movement(
        session,
        product_id,
        quantity_delta,
        reason="adjustment",
        reference=reason,
    )
    log_action(session, "stock_adjustment", f"product_id={product_id} delta={quantity_delta} reason={reason}")

    return adjustment
