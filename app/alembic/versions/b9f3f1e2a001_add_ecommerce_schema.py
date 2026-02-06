"""add_ecommerce_schema

Revision ID: b9f3f1e2a001
Revises: 8ec838294ad6
Create Date: 2026-02-06
"""

from alembic import op
import sqlalchemy as sa


revision = "b9f3f1e2a001"
down_revision = "8ec838294ad6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user", sa.Column("email", sa.String(), nullable=True))
    op.add_column("user", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)

    op.create_table(
        "authtoken",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("token_type", sa.String(length=40), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False),
        sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("modified", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_authtoken_token"), "authtoken", ["token"], unique=True)

    op.create_table("category", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("slug", sa.String(120), nullable=False), sa.Column("parent_id", sa.Integer(), nullable=True), sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True), sa.Column("created", sa.DateTime(timezone=True), nullable=False), sa.Column("modified", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["parent_id"], ["category.id"]))
    op.create_index(op.f("ix_category_slug"), "category", ["slug"], unique=True)

    op.create_table("brand", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("slug", sa.String(120), nullable=False), sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True), sa.Column("created", sa.DateTime(timezone=True), nullable=False), sa.Column("modified", sa.DateTime(timezone=True), nullable=False))
    op.create_index(op.f("ix_brand_slug"), "brand", ["slug"], unique=True)

    op.create_table("product", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("title", sa.String(255), nullable=False), sa.Column("slug", sa.String(255), nullable=False), sa.Column("description", sa.Text(), nullable=True), sa.Column("brand_id", sa.Integer(), nullable=True), sa.Column("category_id", sa.Integer(), nullable=True), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True), sa.Column("created", sa.DateTime(timezone=True), nullable=False), sa.Column("modified", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["brand_id"], ["brand.id"]), sa.ForeignKeyConstraint(["category_id"], ["category.id"]))
    op.create_index(op.f("ix_product_slug"), "product", ["slug"], unique=True)

    op.create_table("productvariant", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("product_id", sa.Integer(), nullable=False), sa.Column("sku", sa.String(80), nullable=False), sa.Column("color", sa.String(50), nullable=True), sa.Column("size", sa.String(50), nullable=True), sa.Column("price", sa.Numeric(12,2), nullable=False), sa.Column("stock", sa.Integer(), nullable=False), sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True), sa.Column("created", sa.DateTime(timezone=True), nullable=False), sa.Column("modified", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["product_id"], ["product.id"]), sa.UniqueConstraint("product_id", "sku", name="uq_variant_product_sku"))

    op.create_table("cart", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), nullable=True), sa.Column("session_token", sa.String(128), nullable=True), sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True), sa.Column("created", sa.DateTime(timezone=True), nullable=False), sa.Column("modified", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["user.id"]))
    op.create_table("cartitem", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("cart_id", sa.Integer(), nullable=False), sa.Column("variant_id", sa.Integer(), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True), sa.Column("created", sa.DateTime(timezone=True), nullable=False), sa.Column("modified", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["cart_id"], ["cart.id"]), sa.ForeignKeyConstraint(["variant_id"], ["productvariant.id"]), sa.UniqueConstraint("cart_id", "variant_id", name="uq_cart_variant"))

    op.create_table("order", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("status", sa.Enum("pending", "paid", "shipped", "completed", "cancelled", "refunded", name="orderstatus"), nullable=False), sa.Column("total_amount", sa.Numeric(12,2), nullable=False), sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True), sa.Column("created", sa.DateTime(timezone=True), nullable=False), sa.Column("modified", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["user.id"]))
    op.create_table("orderitem", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("order_id", sa.Integer(), nullable=False), sa.Column("variant_id", sa.Integer(), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("unit_price", sa.Numeric(12,2), nullable=False), sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True), sa.Column("created", sa.DateTime(timezone=True), nullable=False), sa.Column("modified", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["order_id"], ["order.id"]), sa.ForeignKeyConstraint(["variant_id"], ["productvariant.id"]))
    op.create_table("payment", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("order_id", sa.Integer(), nullable=False), sa.Column("provider", sa.String(50), nullable=False), sa.Column("provider_ref", sa.String(255), nullable=True), sa.Column("status", sa.Enum("pending", "succeeded", "failed", "refunded", name="paymentstatus"), nullable=False), sa.Column("amount", sa.Numeric(12,2), nullable=False), sa.Column("is_deleted", sa.DateTime(timezone=True), nullable=True), sa.Column("created", sa.DateTime(timezone=True), nullable=False), sa.Column("modified", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["order_id"], ["order.id"]))


def downgrade() -> None:
    for table in ["payment", "orderitem", "order", "cartitem", "cart", "productvariant", "product", "brand", "category", "authtoken"]:
        op.drop_table(table)
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_column("user", "email_verified")
    op.drop_column("user", "email")
