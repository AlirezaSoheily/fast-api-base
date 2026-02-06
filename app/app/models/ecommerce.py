"""Ecommerce domain models for catalog, cart, orders, inventory and payments."""

from __future__ import annotations

import enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class OrderStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    shipped = "shipped"
    completed = "completed"
    cancelled = "cancelled"
    refunded = "refunded"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    refunded = "refunded"


class Category(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    parent: Mapped[Category | None] = relationship(remote_side="Category.id")


class Brand(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)


class Product(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text())
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("brand.id"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    brand: Mapped[Brand | None] = relationship()
    category: Mapped[Category | None] = relationship()
    variants: Mapped[list[ProductVariant]] = relationship(back_populates="product")


class ProductVariant(Base):
    __table_args__ = (UniqueConstraint("product_id", "sku", name="uq_variant_product_sku"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), index=True)
    sku: Mapped[str] = mapped_column(String(80), index=True)
    color: Mapped[str | None] = mapped_column(String(50))
    size: Mapped[str | None] = mapped_column(String(50))
    price: Mapped[float] = mapped_column(Numeric(12, 2))
    stock: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped[Product] = relationship(back_populates="variants")


class Cart(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), index=True)
    session_token: Mapped[str | None] = mapped_column(String(128), index=True)


class CartItem(Base):
    __table_args__ = (
        UniqueConstraint("cart_id", "variant_id", name="uq_cart_variant"),
        CheckConstraint("quantity > 0", name="ck_cart_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("cart.id"), index=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("productvariant.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)


class Order(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.pending)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    tracking_code: Mapped[str | None] = mapped_column(String(120))
    shipping_address: Mapped[str] = mapped_column(String(500), default="")
    postal_code: Mapped[str] = mapped_column(String(20), default="")


class OrderItem(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"), index=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("productvariant.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2))


class Payment(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"), index=True)
    provider: Mapped[str] = mapped_column(String(50), default="sandbox")
    provider_ref: Mapped[str | None] = mapped_column(String(255), index=True)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.pending
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2))


class AuthToken(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    token_type: Mapped[str] = mapped_column(String(40), index=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
