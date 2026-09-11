from decimal import Decimal

import pytest

from app.data.db import create_db_engine, init_db, make_session_factory
from app.security.session_context import get_current_user, set_current_user
from app.services.audit import recent_audit_log
from app.services.auth import create_user
from app.services.master_data import create_product, delete_reference, set_product_active
from app.services.transactions import create_adjustment
from app.data.models import Category


@pytest.fixture()
def session():
    engine = create_db_engine(db_path=":memory:")
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as s:
        yield s


@pytest.fixture(autouse=True)
def reset_current_user():
    previous = get_current_user()
    set_current_user(None)
    yield
    set_current_user(previous)


def test_actions_are_attributed_to_the_logged_in_user(session):
    admin = create_user(session, "admin", "password", role="admin")
    session.commit()
    set_current_user(admin)

    category = Category(name="Snacks")
    session.add(category)
    session.flush()
    delete_reference(session, Category, category.id)
    session.commit()

    entries = recent_audit_log(session)
    log, user = entries[0]
    assert log.action == "reference_deleted"
    assert user.username == "admin"


def test_stock_adjustment_is_audited(session):
    product = create_product(
        session, sku="SKU-1", name="Widget", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("2"),
        reorder_level=Decimal("0"), opening_stock=Decimal("10"),
    )
    session.commit()

    create_adjustment(session, product.id, Decimal("-2"), reason="damaged in transit")
    session.commit()

    entries = recent_audit_log(session)
    actions = [log.action for log, _ in entries]
    assert "stock_adjustment" in actions


def test_product_deactivation_is_audited(session):
    product = create_product(
        session, sku="SKU-2", name="Gadget", category_id=None, unit_id=None,
        location_id=None, purchase_price=Decimal("1"), sale_price=Decimal("2"),
        reorder_level=Decimal("0"), opening_stock=Decimal("0"),
    )
    session.commit()

    set_product_active(session, product.id, False)
    session.commit()

    entries = recent_audit_log(session)
    actions = [log.action for log, _ in entries]
    assert "product_status_changed" in actions


def test_audit_entry_has_no_user_when_nobody_is_logged_in(session):
    category = Category(name="Beverages")
    session.add(category)
    session.flush()
    delete_reference(session, Category, category.id)
    session.commit()

    log, user = recent_audit_log(session)[0]
    assert user is None
