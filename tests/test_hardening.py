import time
from decimal import Decimal

import pytest

from app.data.db import create_db_engine, init_db, make_session_factory
from app.data.models import Product, StockTransaction
from app.services.master_data import (
    InvalidProductDataError,
    create_product,
)
from app.services.reports import dashboard_summary
from app.services.stock_ledger import record_movement
from app.services.transactions import (
    EmptyTransactionError,
    InvalidLineItemError,
    LineItem,
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


# --- boundary: invalid data --------------------------------------------

def test_negative_purchase_price_rejected(session):
    with pytest.raises(InvalidProductDataError):
        create_product(
            session, sku="SKU-NEG", name="Bad", category_id=None, unit_id=None,
            location_id=None, purchase_price=Decimal("-1"), sale_price=Decimal("2"),
            reorder_level=Decimal("0"), opening_stock=Decimal("0"),
        )


def test_negative_reorder_level_rejected(session):
    with pytest.raises(InvalidProductDataError):
        create_product(
            session, sku="SKU-NEG2", name="Bad", category_id=None, unit_id=None,
            location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("2"),
            reorder_level=Decimal("-5"), opening_stock=Decimal("0"),
        )


def test_negative_opening_stock_rejected(session):
    with pytest.raises(InvalidProductDataError):
        create_product(
            session, sku="SKU-NEG3", name="Bad", category_id=None, unit_id=None,
            location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("2"),
            reorder_level=Decimal("0"), opening_stock=Decimal("-10"),
        )


def test_zero_or_negative_line_item_quantity_rejected(session):
    product = create_product(
        session, sku="SKU-1", name="Widget", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("2"),
        reorder_level=Decimal("0"), opening_stock=Decimal("100"),
    )
    with pytest.raises(InvalidLineItemError):
        create_sale(session, customer_id=None, reference="S1",
                    items=[LineItem(product.id, Decimal("0"), Decimal("2"))])
    with pytest.raises(InvalidLineItemError):
        create_sale(session, customer_id=None, reference="S2",
                    items=[LineItem(product.id, Decimal("-5"), Decimal("2"))])


def test_negative_line_item_price_rejected(session):
    product = create_product(
        session, sku="SKU-2", name="Widget", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("2"),
        reorder_level=Decimal("0"), opening_stock=Decimal("10"),
    )
    with pytest.raises(InvalidLineItemError):
        create_purchase(session, supplier_id=None, reference="P1",
                         items=[LineItem(product.id, Decimal("5"), Decimal("-1"))])


def test_duplicate_sku_and_barcode_both_rejected(session):
    create_product(
        session, sku="DUP-1", name="First", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("2"),
        reorder_level=Decimal("0"), opening_stock=Decimal("0"), barcode="BC-1",
    )
    from app.services.master_data import DuplicateSkuError
    with pytest.raises(DuplicateSkuError):
        create_product(
            session, sku="DUP-1", name="Second", category_id=None, unit_id=None,
            location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("2"),
            reorder_level=Decimal("0"), opening_stock=Decimal("0"),
        )
    # Barcode uniqueness is enforced at the database level (unique constraint).
    from sqlalchemy.exc import IntegrityError
    session.flush()
    dup_barcode = Product(sku="DUP-2", name="Third", barcode="BC-1", current_stock=Decimal("0"))
    session.add(dup_barcode)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


# --- boundary: huge quantities and exact decimal math -------------------

def test_very_large_quantity_is_handled_exactly(session):
    product = create_product(
        session, sku="SKU-BIG", name="Bulk Item", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("0.01"), sale_price=Decimal("0.02"),
        reorder_level=Decimal("0"), opening_stock=Decimal("0"),
    )
    huge_qty = Decimal("999999999.99")
    create_purchase(session, supplier_id=None, reference="BIG-1",
                     items=[LineItem(product.id, huge_qty, Decimal("0.01"))])
    session.refresh(product)
    assert product.current_stock == huge_qty


def test_many_small_fractional_movements_sum_exactly(session):
    product = create_product(
        session, sku="SKU-FRAC", name="Fractional", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("1"),
        reorder_level=Decimal("0"), opening_stock=Decimal("0"),
    )
    for _ in range(1000):
        record_movement(session, product.id, Decimal("0.01"), reason="purchase")
    session.refresh(product)
    assert product.current_stock == Decimal("10.00")


# --- "power loss": a failure mid-transaction must not leave partial data --

def test_failed_purchase_leaves_no_partial_ledger_entries(session):
    good_product = create_product(
        session, sku="SKU-GOOD", name="Good", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("2"),
        reorder_level=Decimal("0"), opening_stock=Decimal("10"),
    )
    session.commit()

    # Second line item references a nonexistent product, simulating a
    # failure partway through a multi-item transaction.
    with pytest.raises(Exception):
        create_purchase(
            session, supplier_id=None, reference="MIXED",
            items=[
                LineItem(good_product.id, Decimal("5"), Decimal("1")),
                LineItem(999999, Decimal("5"), Decimal("1")),
            ],
        )
    session.rollback()

    session.refresh(good_product)
    assert good_product.current_stock == Decimal("10")  # unchanged
    ledger_count = len(
        session.query(StockTransaction).filter_by(product_id=good_product.id).all()
    )
    assert ledger_count == 1  # only the original opening_stock entry


def test_rolled_back_session_does_not_persist_new_product(session):
    create_product(
        session, sku="SKU-ROLLBACK", name="Should not persist", category_id=None,
        unit_id=None, location_id=None, purchase_price=Decimal("1"),
        sale_price=Decimal("2"), reorder_level=Decimal("0"), opening_stock=Decimal("5"),
    )
    session.rollback()

    from sqlalchemy import select
    result = session.scalar(select(Product).where(Product.sku == "SKU-ROLLBACK"))
    assert result is None


# --- performance sanity check -------------------------------------------

def test_bulk_data_performance_is_reasonable(session):
    """Not a strict benchmark - just confirms the app doesn't fall over or
    become unusably slow at a realistic small-business inventory size."""
    products = []
    for i in range(300):
        p = create_product(
            session, sku=f"PERF-{i:04d}", name=f"Product {i}", category_id=None,
            unit_id=None, location_id=None, purchase_price=Decimal("10"),
            sale_price=Decimal("15"), reorder_level=Decimal("5"),
            opening_stock=Decimal("100"),
        )
        products.append(p)
    session.commit()

    start = time.perf_counter()
    for i in range(1000):
        product = products[i % len(products)]
        record_movement(session, product.id, Decimal("-1"), reason="sale")
    session.commit()
    elapsed = time.perf_counter() - start

    summary = dashboard_summary(session)
    assert summary.product_count == 300
    assert elapsed < 10, f"1000 stock movements took {elapsed:.2f}s, expected under 10s"
