from decimal import Decimal

from sqlalchemy.types import String, TypeDecorator


class SqliteDecimal(TypeDecorator):
    """Stores Decimal values as exact strings.

    SQLite has no native fixed-point type, and SQLAlchemy's Numeric falls
    back to Python floats there, which introduces binary floating-point
    rounding error for money/quantity fields. Storing as a string keeps the
    value exact on both write and read.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(Decimal(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return Decimal(value)
