"""add is_active to categories/units/locations/suppliers/customers

Revision ID: 7a1c9e2f5b3d
Revises: 3b86235d4b5e
Create Date: 2026-09-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a1c9e2f5b3d'
down_revision: Union[str, None] = '3b86235d4b5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ("categories", "units", "locations", "suppliers", "customers")


def upgrade() -> None:
    for table in TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(
                sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true())
            )


def downgrade() -> None:
    for table in TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_column('is_active')
