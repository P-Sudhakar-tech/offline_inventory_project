from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.data.models.base import Base
from app.data.models.types import SqliteDecimal


class StockTransaction(Base):
    """Immutable stock movement ledger.

    Every receipt, issue, sale, damage, return, or adjustment creates one
    row here. This is the source of truth; Product.current_stock is only a
    cached projection for fast display and must always be derivable by
    summing qty_delta for a product.
    """

    __tablename__ = "stock_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    qty_delta: Mapped[Decimal] = mapped_column(SqliteDecimal, nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(SqliteDecimal, nullable=False)

    reason: Mapped[str] = mapped_column(String(60), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(200))

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
