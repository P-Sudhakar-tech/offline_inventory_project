"""merge product purchase_price/sale_price into a single price column

Revision ID: 3b86235d4b5e
Revises: fe4783f90f4f
Create Date: 2026-09-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import app.data.models.types


# revision identifiers, used by Alembic.
revision: str = '3b86235d4b5e'
down_revision: Union[str, None] = 'fe4783f90f4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('price', app.data.models.types.SqliteDecimal(), nullable=True))

    op.execute('UPDATE products SET price = sale_price')

    with op.batch_alter_table('products') as batch_op:
        batch_op.alter_column('price', nullable=False)
        batch_op.drop_column('purchase_price')
        batch_op.drop_column('sale_price')


def downgrade() -> None:
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('purchase_price', app.data.models.types.SqliteDecimal(), nullable=True))
        batch_op.add_column(sa.Column('sale_price', app.data.models.types.SqliteDecimal(), nullable=True))

    op.execute('UPDATE products SET purchase_price = price, sale_price = price')

    with op.batch_alter_table('products') as batch_op:
        batch_op.alter_column('purchase_price', nullable=False)
        batch_op.alter_column('sale_price', nullable=False)
        batch_op.drop_column('price')
