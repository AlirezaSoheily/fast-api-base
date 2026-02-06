"""add phone auth fields and order tracking

Revision ID: c1a2b3d4e5f6
Revises: b9f3f1e2a001
Create Date: 2026-02-06
"""

from alembic import op
import sqlalchemy as sa


revision = "c1a2b3d4e5f6"
down_revision = "b9f3f1e2a001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user", sa.Column("phone_number", sa.String(length=20), nullable=True))
    op.create_index(op.f("ix_user_phone_number"), "user", ["phone_number"], unique=True)
    op.execute("UPDATE \"user\" SET phone_number = username WHERE phone_number IS NULL")
    op.alter_column("user", "phone_number", nullable=False)
    op.add_column("order", sa.Column("tracking_code", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("order", "tracking_code")
    op.drop_index(op.f("ix_user_phone_number"), table_name="user")
    op.drop_column("user", "phone_number")
