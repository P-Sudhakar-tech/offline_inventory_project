from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.data.models import Product, StockTransaction


@dataclass
class DashboardSummary:
    product_count: int
    total_stock_value: Decimal
    low_stock_count: int
    out_of_stock_count: int


def dashboard_summary(session: Session) -> DashboardSummary:
    products = session.scalars(select(Product).where(Product.is_active.is_(True))).all()

    total_value = sum((p.current_stock * p.sale_price for p in products), Decimal("0"))
    low_stock = sum(1 for p in products if 0 < p.current_stock <= p.reorder_level)
    out_of_stock = sum(1 for p in products if p.current_stock <= 0)

    return DashboardSummary(
        product_count=len(products),
        total_stock_value=total_value,
        low_stock_count=low_stock,
        out_of_stock_count=out_of_stock,
    )


def recent_transactions(session: Session, limit: int = 10):
    stmt = (
        select(StockTransaction, Product)
        .join(Product, Product.id == StockTransaction.product_id)
        .order_by(StockTransaction.created_at.desc(), StockTransaction.id.desc())
        .limit(limit)
    )
    return session.execute(stmt).all()


def current_stock_report(session: Session):
    stmt = select(Product).where(Product.is_active.is_(True)).order_by(Product.name)
    return session.scalars(stmt).all()


def low_stock_report(session: Session):
    products = current_stock_report(session)
    return [p for p in products if 0 < p.current_stock <= p.reorder_level]


def out_of_stock_report(session: Session):
    products = current_stock_report(session)
    return [p for p in products if p.current_stock <= 0]


def product_ledger(session: Session, product_id: int):
    stmt = (
        select(StockTransaction)
        .where(StockTransaction.product_id == product_id)
        .order_by(StockTransaction.created_at, StockTransaction.id)
    )
    return session.scalars(stmt).all()


def stock_movement_report(session: Session, start: datetime, end: datetime):
    stmt = (
        select(StockTransaction, Product)
        .join(Product, Product.id == StockTransaction.product_id)
        .where(StockTransaction.created_at >= start, StockTransaction.created_at <= end)
        .order_by(StockTransaction.created_at)
    )
    return session.execute(stmt).all()
