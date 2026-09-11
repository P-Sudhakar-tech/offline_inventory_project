from decimal import Decimal

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.data.models.base import Base
from app.data.models.types import SqliteDecimal


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.id"))
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))

    purchase_price: Mapped[Decimal] = mapped_column(SqliteDecimal, default=Decimal("0"))
    sale_price: Mapped[Decimal] = mapped_column(SqliteDecimal, default=Decimal("0"))

    reorder_level: Mapped[Decimal] = mapped_column(SqliteDecimal, default=Decimal("0"))
    current_stock: Mapped[Decimal] = mapped_column(SqliteDecimal, default=Decimal("0"))

    is_active: Mapped[bool] = mapped_column(default=True)
