from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.models import Category, Customer, Location, Product, Supplier, Unit
from app.services.audit import log_action
from app.services.stock_ledger import record_movement


class DuplicateNameError(Exception):
    pass


class DuplicateSkuError(Exception):
    pass


class InvalidProductDataError(Exception):
    pass


def _validate_product_fields(purchase_price: Decimal, sale_price: Decimal, reorder_level: Decimal) -> None:
    if purchase_price < 0 or sale_price < 0 or reorder_level < 0:
        raise InvalidProductDataError("Prices and reorder level cannot be negative")


# --- generic name-only reference data (Category, Unit, Location) ---------

def list_reference(session: Session, model):
    return session.scalars(select(model).order_by(model.name)).all()


def create_reference(session: Session, model, name: str):
    name = name.strip()
    existing = session.scalar(select(model).where(model.name == name))
    if existing is not None:
        raise DuplicateNameError(f"{model.__name__} '{name}' already exists")
    row = model(name=name)
    session.add(row)
    session.flush()
    return row


def rename_reference(session: Session, model, row_id: int, new_name: str):
    new_name = new_name.strip()
    existing = session.scalar(
        select(model).where(model.name == new_name, model.id != row_id)
    )
    if existing is not None:
        raise DuplicateNameError(f"{model.__name__} '{new_name}' already exists")
    row = session.get(model, row_id)
    row.name = new_name
    session.flush()
    return row


def delete_reference(session: Session, model, row_id: int):
    row = session.get(model, row_id)
    if row is not None:
        log_action(session, "reference_deleted", f"{model.__name__} id={row_id} name={row.name}")
        session.delete(row)
        session.flush()


# --- suppliers / customers ------------------------------------------------

def list_suppliers(session: Session):
    return session.scalars(select(Supplier).order_by(Supplier.name)).all()


def save_supplier(session: Session, supplier_id: int | None, name: str, contact: str, address: str):
    if supplier_id is None:
        row = Supplier(name=name.strip(), contact=contact.strip() or None, address=address.strip() or None)
        session.add(row)
    else:
        row = session.get(Supplier, supplier_id)
        row.name = name.strip()
        row.contact = contact.strip() or None
        row.address = address.strip() or None
    session.flush()
    return row


def delete_supplier(session: Session, supplier_id: int):
    row = session.get(Supplier, supplier_id)
    if row is not None:
        log_action(session, "supplier_deleted", f"id={supplier_id} name={row.name}")
        session.delete(row)
        session.flush()


def list_customers(session: Session):
    return session.scalars(select(Customer).order_by(Customer.name)).all()


def save_customer(session: Session, customer_id: int | None, name: str, contact: str):
    if customer_id is None:
        row = Customer(name=name.strip(), contact=contact.strip() or None)
        session.add(row)
    else:
        row = session.get(Customer, customer_id)
        row.name = name.strip()
        row.contact = contact.strip() or None
    session.flush()
    return row


def delete_customer(session: Session, customer_id: int):
    row = session.get(Customer, customer_id)
    if row is not None:
        log_action(session, "customer_deleted", f"id={customer_id} name={row.name}")
        session.delete(row)
        session.flush()


# --- products --------------------------------------------------------------

def list_products(session: Session, include_inactive: bool = False):
    stmt = select(Product).order_by(Product.name)
    if not include_inactive:
        stmt = stmt.where(Product.is_active.is_(True))
    return session.scalars(stmt).all()


def create_product(
    session: Session,
    sku: str,
    name: str,
    category_id: int | None,
    unit_id: int | None,
    location_id: int | None,
    purchase_price: Decimal,
    sale_price: Decimal,
    reorder_level: Decimal,
    opening_stock: Decimal,
    barcode: str | None = None,
) -> Product:
    sku = sku.strip()
    _validate_product_fields(purchase_price, sale_price, reorder_level)
    if opening_stock < 0:
        raise InvalidProductDataError("Opening stock cannot be negative")
    existing = session.scalar(select(Product).where(Product.sku == sku))
    if existing is not None:
        raise DuplicateSkuError(f"SKU '{sku}' already exists")

    product = Product(
        sku=sku,
        barcode=(barcode or "").strip() or None,
        name=name.strip(),
        category_id=category_id,
        unit_id=unit_id,
        location_id=location_id,
        purchase_price=purchase_price,
        sale_price=sale_price,
        reorder_level=reorder_level,
        current_stock=Decimal("0"),
        is_active=True,
    )
    session.add(product)
    session.flush()

    if opening_stock and opening_stock != 0:
        record_movement(session, product.id, opening_stock, reason="opening_stock")

    return product


def update_product(
    session: Session,
    product_id: int,
    sku: str,
    name: str,
    category_id: int | None,
    unit_id: int | None,
    location_id: int | None,
    purchase_price: Decimal,
    sale_price: Decimal,
    reorder_level: Decimal,
    barcode: str | None = None,
) -> Product:
    sku = sku.strip()
    _validate_product_fields(purchase_price, sale_price, reorder_level)
    existing = session.scalar(
        select(Product).where(Product.sku == sku, Product.id != product_id)
    )
    if existing is not None:
        raise DuplicateSkuError(f"SKU '{sku}' already exists")

    product = session.get(Product, product_id)
    product.sku = sku
    product.barcode = (barcode or "").strip() or None
    product.name = name.strip()
    product.category_id = category_id
    product.unit_id = unit_id
    product.location_id = location_id
    product.purchase_price = purchase_price
    product.sale_price = sale_price
    product.reorder_level = reorder_level
    session.flush()
    return product


def set_product_active(session: Session, product_id: int, is_active: bool):
    """Products are never hard-deleted once they may have transactions; toggle status instead."""
    product = session.get(Product, product_id)
    product.is_active = is_active
    log_action(session, "product_status_changed", f"sku={product.sku} is_active={is_active}")
    session.flush()
    return product
