from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.data.models.base import Base

ROLES = ["admin", "manager", "operator", "viewer"]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    salt: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="operator")
    is_active: Mapped[bool] = mapped_column(default=True)
