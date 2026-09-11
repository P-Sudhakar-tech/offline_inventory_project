from decimal import Decimal

import pytest

from app.data.db import create_db_engine, init_db, make_session_factory
from app.services.master_data import create_product
from app.services.stock_ledger import InsufficientStockError
from app.services.transactions import (
    EmptyTransactionError,
    LineItem,
    create_adjustment,
    create_purchase,
    create_sale,
)


@pytest.fixture()
def session():
    engine = create_db_engine(db_path=":memory:")
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as s:
        yield s


def _product(session, opening=Decimal("0")):
    return create_product(
        session, sku="SKU-1", name="Widget", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("10"), sale_price=Decimal("15"),
        reorder_level=Decimal("5"), opening_stock=opening,
    )


def test_purchase_increases_stock(session):
    product = _product(session, opening=Decimal("0"))
    create_purchase(
        session, supplier_id=None, reference="INV-1",
        items=[LineItem(product.id, Decimal("30"), Decimal("10"))],
    )
    session.commit()
    session.refresh(product)
    assert product.current_stock == Decimal("30")


def test_sale_decreases_stock(session):
    product = _product(session, opening=Decimal("50"))
    create_sale(
        session, customer_id=None, reference="SALE-1",
        items=[LineItem(product.id, Decimal("20"), Decimal("15"))],
    )
    session.commit()
    session.refresh(product)
    assert product.current_stock == Decimal("30")


def test_sale_blocked_when_insufficient_stock(session):
    product = _product(session, opening=Decimal("5"))
    with pytest.raises(InsufficientStockError):
        create_sale(
            session, customer_id=None, reference="SALE-2",
            items=[LineItem(product.id, Decimal("10"), Decimal("15"))],
        )


def test_purchase_requires_at_least_one_item(session):
    with pytest.raises(EmptyTransactionError):
        create_purchase(session, supplier_id=None, reference="INV-EMPTY", items=[])


def test_adjustment_requires_reason(session):
    product = _product(session, opening=Decimal("10"))
    with pytest.raises(ValueError):
        create_adjustment(session, product.id, Decimal("-2"), reason="   ")


def test_adjustment_updates_ledger_and_stock(session):
    product = _product(session, opening=Decimal("10"))
    create_adjustment(session, product.id, Decimal("-3"), reason="physical count shortage")
    session.commit()
    session.refresh(product)
    assert product.current_stock == Decimal("7")
