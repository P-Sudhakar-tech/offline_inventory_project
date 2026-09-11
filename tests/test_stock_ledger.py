from decimal import Decimal

import pytest

from app.data.db import create_db_engine, init_db, make_session_factory
from app.data.models import Product
from app.services.stock_ledger import (
    InsufficientStockError,
    ProductNotFoundError,
    record_movement,
)


@pytest.fixture()
def session():
    engine = create_db_engine(db_path=":memory:")
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as s:
        yield s


def _make_product(session, sku="SKU-1", opening=Decimal("0")):
    product = Product(sku=sku, name="Test Product", current_stock=opening)
    session.add(product)
    session.flush()
    return product


def test_example_movement_sequence_from_plan(session):
    product = _make_product(session, opening=Decimal("100"))

    record_movement(session, product.id, Decimal("50"), reason="purchase")
    record_movement(session, product.id, Decimal("-20"), reason="sale")
    record_movement(session, product.id, Decimal("-2"), reason="damage")
    session.commit()

    session.refresh(product)
    assert product.current_stock == Decimal("128")


def test_ledger_matches_cached_balance(session):
    product = _make_product(session, opening=Decimal("10"))
    record_movement(session, product.id, Decimal("5"), reason="purchase")
    record_movement(session, product.id, Decimal("-3"), reason="sale")
    session.commit()

    from sqlalchemy import select
    from app.data.models.stock_transaction import StockTransaction

    rows = session.scalars(
        select(StockTransaction).where(StockTransaction.product_id == product.id)
    ).all()
    total_delta = sum((r.qty_delta for r in rows), Decimal("0"))

    session.refresh(product)
    assert product.current_stock == Decimal("10") + total_delta


def test_negative_stock_blocked_by_default(session):
    product = _make_product(session, opening=Decimal("5"))
    with pytest.raises(InsufficientStockError):
        record_movement(session, product.id, Decimal("-10"), reason="sale")


def test_negative_stock_allowed_when_flagged(session):
    product = _make_product(session, opening=Decimal("5"))
    record_movement(session, product.id, Decimal("-10"), reason="sale", allow_negative=True)
    session.refresh(product)
    assert product.current_stock == Decimal("-5")


def test_unknown_product_raises(session):
    with pytest.raises(ProductNotFoundError):
        record_movement(session, 999, Decimal("1"), reason="purchase")


def test_decimal_precision_is_exact(session):
    product = _make_product(session, opening=Decimal("0.1"))
    record_movement(session, product.id, Decimal("0.2"), reason="purchase")
    session.refresh(product)
    assert product.current_stock == Decimal("0.3")
