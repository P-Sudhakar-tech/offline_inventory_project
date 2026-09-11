from decimal import Decimal

import pytest

from app.data.db import create_db_engine, init_db, make_session_factory
from app.data.models import Category
from app.services.master_data import (
    DuplicateNameError,
    DuplicateSkuError,
    create_product,
    create_reference,
    list_products,
    set_product_active,
    update_product,
)


@pytest.fixture()
def session():
    engine = create_db_engine(db_path=":memory:")
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as s:
        yield s


def test_create_reference_rejects_duplicate_name(session):
    create_reference(session, Category, "Beverages")
    with pytest.raises(DuplicateNameError):
        create_reference(session, Category, "Beverages")


def test_create_product_rejects_duplicate_sku(session):
    create_product(
        session, sku="SKU-1", name="Widget", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("2"),
        reorder_level=Decimal("0"), opening_stock=Decimal("0"),
    )
    with pytest.raises(DuplicateSkuError):
        create_product(
            session, sku="SKU-1", name="Other", category_id=None, unit_id=None,
            location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("2"),
            reorder_level=Decimal("0"), opening_stock=Decimal("0"),
        )


def test_create_product_with_opening_stock_creates_ledger_entry(session):
    product = create_product(
        session, sku="SKU-2", name="Gadget", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("5"), sale_price=Decimal("9"),
        reorder_level=Decimal("2"), opening_stock=Decimal("40"),
    )
    session.commit()
    session.refresh(product)
    assert product.current_stock == Decimal("40")


def test_deactivate_product_does_not_delete_it(session):
    product = create_product(
        session, sku="SKU-3", name="Thing", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("1"),
        reorder_level=Decimal("0"), opening_stock=Decimal("0"),
    )
    set_product_active(session, product.id, False)
    session.commit()

    active_only = list_products(session)
    everything = list_products(session, include_inactive=True)
    assert product.id not in [p.id for p in active_only]
    assert product.id in [p.id for p in everything]


def test_update_product_rejects_sku_collision_with_other_product(session):
    p1 = create_product(
        session, sku="SKU-A", name="A", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("1"),
        reorder_level=Decimal("0"), opening_stock=Decimal("0"),
    )
    p2 = create_product(
        session, sku="SKU-B", name="B", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("1"),
        reorder_level=Decimal("0"), opening_stock=Decimal("0"),
    )
    with pytest.raises(DuplicateSkuError):
        update_product(
            session, p2.id, sku="SKU-A", name="B", category_id=None, unit_id=None,
            location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("1"),
            reorder_level=Decimal("0"),
        )
