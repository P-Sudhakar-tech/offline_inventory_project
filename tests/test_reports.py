from decimal import Decimal

import pytest

from app.data.db import create_db_engine, init_db, make_session_factory
from app.services.master_data import create_product
from app.services.reports import (
    dashboard_summary,
    low_stock_report,
    out_of_stock_report,
    product_ledger,
    recent_transactions,
)
from app.services.transactions import LineItem, create_sale


@pytest.fixture()
def session():
    engine = create_db_engine(db_path=":memory:")
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as s:
        yield s


def test_dashboard_summary_counts_low_and_out_of_stock(session):
    healthy = create_product(
        session, sku="SKU-H", name="Healthy", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("5"), sale_price=Decimal("10"),
        reorder_level=Decimal("5"), opening_stock=Decimal("100"),
    )
    low = create_product(
        session, sku="SKU-L", name="Low", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("5"), sale_price=Decimal("10"),
        reorder_level=Decimal("10"), opening_stock=Decimal("3"),
    )
    out = create_product(
        session, sku="SKU-O", name="Out", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("5"), sale_price=Decimal("10"),
        reorder_level=Decimal("5"), opening_stock=Decimal("0"),
    )
    session.commit()

    summary = dashboard_summary(session)
    assert summary.product_count == 3
    assert summary.low_stock_count == 1
    assert summary.out_of_stock_count == 1
    assert summary.total_stock_value == Decimal("100") * Decimal("10") + Decimal("3") * Decimal("10")

    low_rows = low_stock_report(session)
    out_rows = out_of_stock_report(session)
    assert [p.id for p in low_rows] == [low.id]
    assert [p.id for p in out_rows] == [out.id]


def test_product_ledger_reflects_all_movements_in_order(session):
    product = create_product(
        session, sku="SKU-1", name="Widget", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("5"), sale_price=Decimal("10"),
        reorder_level=Decimal("5"), opening_stock=Decimal("20"),
    )
    create_sale(session, customer_id=None, reference="S1", items=[LineItem(product.id, Decimal("5"), Decimal("10"))])
    session.commit()

    ledger = product_ledger(session, product.id)
    assert [t.reason for t in ledger] == ["opening_stock", "sale"]
    assert [t.balance_after for t in ledger] == [Decimal("20"), Decimal("15")]


def test_recent_transactions_returns_product_pairs(session):
    product = create_product(
        session, sku="SKU-1", name="Widget", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("5"), sale_price=Decimal("10"),
        reorder_level=Decimal("5"), opening_stock=Decimal("20"),
    )
    session.commit()

    rows = recent_transactions(session, limit=5)
    assert len(rows) == 1
    txn, prod = rows[0]
    assert prod.id == product.id
    assert txn.reason == "opening_stock"
