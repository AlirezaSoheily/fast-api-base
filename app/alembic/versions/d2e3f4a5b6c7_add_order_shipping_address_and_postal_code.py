"""add order shipping address and postal code

Revision ID: d2e3f4a5b6c7
Revises: c1a2b3d4e5f6
Create Date: 2026-02-06
"""

from alembic import op
import sqlalchemy as sa


revision = "d2e3f4a5b6c7"
down_revision = "c1a2b3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("order", sa.Column("shipping_address", sa.String(length=500), nullable=True))
    op.add_column("order", sa.Column("postal_code", sa.String(length=20), nullable=True))
    op.execute("UPDATE \"order\" SET shipping_address = '' WHERE shipping_address IS NULL")
    op.execute("UPDATE \"order\" SET postal_code = '' WHERE postal_code IS NULL")
    op.alter_column("order", "shipping_address", nullable=False)
    op.alter_column("order", "postal_code", nullable=False)


def downgrade() -> None:
    op.drop_column("order", "postal_code")
    op.drop_column("order", "shipping_address")
