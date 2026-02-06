"""Core ecommerce service functions."""

from __future__ import annotations

import secrets
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import exceptions, models
from app.core.security import JWTHandler
from app.schemas.ecommerce import ProductFilter
from app.utils import MessageCodes


async def request_register_otp(db: AsyncSession, phone_number: str) -> str:
    result = await db.execute(select(models.User).where(models.User.phone_number == phone_number))
    user = result.scalar_one_or_none()
    if user and user.is_active:
        raise exceptions.AlreadyExistException(
            detail="Phone number is already registered",
            msg_code=MessageCodes.already_exist_object,
        )

    if not user:
        user = models.User(
            username=phone_number,
            email=None,
            full_name=None,
            phone_number=phone_number,
            hashed_password="otp-register",
            is_active=False,
            roles=[models.UserRoles.Consumer],
        )
        db.add(user)
        await db.flush()

    otp_code = f"{secrets.randbelow(900000) + 100000}"
    db.add(
        models.AuthToken(
            user_id=user.id,
            token=f"register:{phone_number}:{otp_code}",
            token_type="register_otp",
        )
    )
    await db.commit()
    return otp_code


async def register_user(
    db: AsyncSession,
    *,
    phone_number: str,
    otp_code: str,
    full_name: str | None,
    email: str | None,
) -> models.User:
    result = await db.execute(
        select(models.AuthToken)
        .where(
            and_(
                models.AuthToken.token == f"register:{phone_number}:{otp_code}",
                models.AuthToken.token_type == "register_otp",
                models.AuthToken.is_used.is_(False),
            )
        )
        .order_by(models.AuthToken.created.desc())
    )
    otp_token = result.scalar_one_or_none()
    if not otp_token:
        raise exceptions.ValidationException(
            detail="Invalid registration OTP",
            msg_code=MessageCodes.bad_request,
        )

    user = await db.get(models.User, otp_token.user_id)
    if not user or user.phone_number != phone_number:
        raise exceptions.ValidationException(
            detail="Phone number mismatch for registration",
            msg_code=MessageCodes.bad_request,
        )

    otp_token.is_used = True
    user.full_name = full_name
    user.email = email
    user.is_active = True
    db.add_all([otp_token, user])
    await db.commit()
    await db.refresh(user)
    return user


async def request_login_otp(db: AsyncSession, phone_number: str) -> str:
    result = await db.execute(select(models.User).where(models.User.phone_number == phone_number))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise exceptions.NotFoundException(
            detail="Registered active user not found for this phone number",
            msg_code=MessageCodes.not_found,
        )

    otp_code = f"{secrets.randbelow(900000) + 100000}"
    db.add(
        models.AuthToken(
            user_id=user.id,
            token=f"login:{phone_number}:{otp_code}",
            token_type="login_otp",
        )
    )
    await db.commit()
    return otp_code


async def login_with_otp(db: AsyncSession, *, phone_number: str, otp_code: str) -> tuple[str, str]:
    result = await db.execute(
        select(models.AuthToken)
        .where(
            and_(
                models.AuthToken.token == f"login:{phone_number}:{otp_code}",
                models.AuthToken.token_type == "login_otp",
                models.AuthToken.is_used.is_(False),
            )
        )
        .order_by(models.AuthToken.created.desc())
    )
    otp_token = result.scalar_one_or_none()
    if not otp_token:
        raise exceptions.ValidationException(
            detail="Invalid login OTP",
            msg_code=MessageCodes.bad_request,
        )
    user = await db.get(models.User, otp_token.user_id)
    if not user:
        raise exceptions.NotFoundException(detail="User not found", msg_code=MessageCodes.not_found)

    otp_token.is_used = True
    access = JWTHandler.encode(payload={"sub": "access", "id": str(user.id)})
    refresh = JWTHandler.encode(payload={"sub": "refresh", "id": str(user.id)})
    db.add(models.AuthToken(user_id=user.id, token=refresh, token_type="refresh"))
    await db.commit()
    return access, refresh


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
    payload = JWTHandler.decode(refresh_token)
    if payload.get("sub") != "refresh":
        raise exceptions.ValidationException(detail="invalid_refresh", msg_code=MessageCodes.bad_request)
    res = await db.execute(
        select(models.AuthToken).where(
            and_(
                models.AuthToken.token == refresh_token,
                models.AuthToken.token_type == "refresh",
                models.AuthToken.is_used.is_(False),
            )
        )
    )
    token_row = res.scalar_one_or_none()
    if not token_row:
        raise exceptions.ValidationException(detail="revoked", msg_code=MessageCodes.bad_request)
    token_row.is_used = True
    new_access = JWTHandler.encode(payload={"sub": "access", "id": payload["id"]})
    new_refresh = JWTHandler.encode(payload={"sub": "refresh", "id": payload["id"]})
    db.add(models.AuthToken(user_id=int(payload["id"]), token=new_refresh, token_type="refresh"))
    await db.commit()
    return new_access, new_refresh


async def list_products(db: AsyncSession, filters: ProductFilter) -> list[models.Product]:
    query = select(models.Product).where(models.Product.is_active.is_(True))
    if filters.search:
        query = query.where(func.lower(models.Product.title).contains(filters.search.lower()))
    if filters.category_id:
        query = query.where(models.Product.category_id == filters.category_id)
    if filters.brand_id:
        query = query.where(models.Product.brand_id == filters.brand_id)
    query = query.offset((filters.page - 1) * filters.size).limit(filters.size)
    result = await db.execute(query)
    return result.scalars().unique().all()


async def add_to_cart(db: AsyncSession, *, user_id: int | None, session_token: str | None, variant_id: int, quantity: int):
    query = select(models.Cart)
    if user_id:
        query = query.where(models.Cart.user_id == user_id)
    else:
        query = query.where(models.Cart.session_token == session_token)
    cart = (await db.execute(query)).scalar_one_or_none()
    if not cart:
        cart = models.Cart(user_id=user_id, session_token=session_token)
        db.add(cart)
        await db.flush()
    item = (
        await db.execute(
            select(models.CartItem).where(
                and_(models.CartItem.cart_id == cart.id, models.CartItem.variant_id == variant_id)
            )
        )
    ).scalar_one_or_none()
    if item:
        item.quantity += quantity
    else:
        db.add(models.CartItem(cart_id=cart.id, variant_id=variant_id, quantity=quantity))
    await db.commit()


async def get_cart(db: AsyncSession, *, user_id: int | None, session_token: str | None):
    query = select(models.Cart)
    query = (
        query.where(models.Cart.user_id == user_id)
        if user_id
        else query.where(models.Cart.session_token == session_token)
    )
    cart = (await db.execute(query)).scalar_one_or_none()
    if not cart:
        return [], Decimal("0")
    rows = (
        await db.execute(
            select(models.CartItem, models.ProductVariant)
            .join(models.ProductVariant, models.ProductVariant.id == models.CartItem.variant_id)
            .where(models.CartItem.cart_id == cart.id)
        )
    ).all()
    total = Decimal("0")
    items = []
    for item, variant in rows:
        total += Decimal(str(variant.price)) * item.quantity
        items.append((item, variant))
    return items, total


async def checkout(
    db: AsyncSession,
    *,
    user_id: int,
    session_token: str | None,
    shipping_address: str,
    postal_code: str,
) -> tuple[models.Order, models.Payment]:
    items, total = await get_cart(db, user_id=user_id, session_token=session_token)
    order = models.Order(
        user_id=user_id,
        total_amount=total,
        shipping_address=shipping_address,
        postal_code=postal_code,
    )
    db.add(order)
    await db.flush()
    for item, variant in items:
        locked_variant = await db.get(models.ProductVariant, variant.id, with_for_update=True)
        if not locked_variant or locked_variant.stock < item.quantity:
            raise exceptions.ValidationException(detail="insufficient_stock", msg_code=MessageCodes.bad_request)
        locked_variant.stock -= item.quantity
        db.add(
            models.OrderItem(
                order_id=order.id,
                variant_id=variant.id,
                quantity=item.quantity,
                unit_price=variant.price,
            )
        )
    payment = models.Payment(
        order_id=order.id,
        amount=total,
        provider="sandbox",
        provider_ref=secrets.token_hex(12),
    )
    db.add(payment)
    await db.commit()
    await db.refresh(order)
    await db.refresh(payment)
    return order, payment


async def create_category(db: AsyncSession, *, name: str, slug: str, parent_id: int | None) -> models.Category:
    category = models.Category(name=name, slug=slug, parent_id=parent_id)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def create_product(
    db: AsyncSession,
    *,
    title: str,
    slug: str,
    description: str | None,
    brand_id: int | None,
    category_id: int | None,
    price: float,
    sku: str,
    stock: int,
) -> models.Product:
    product = models.Product(
        title=title,
        slug=slug,
        description=description,
        brand_id=brand_id,
        category_id=category_id,
        is_active=True,
    )
    db.add(product)
    await db.flush()
    db.add(models.ProductVariant(product_id=product.id, sku=sku, price=price, stock=stock))
    await db.commit()
    await db.refresh(product)
    return product


async def list_orders(db: AsyncSession) -> list[models.Order]:
    rows = await db.execute(select(models.Order).order_by(models.Order.created.desc()))
    return rows.scalars().all()


async def complete_order(db: AsyncSession, *, order_id: int, tracking_code: str) -> models.Order:
    order = await db.get(models.Order, order_id)
    if not order:
        raise exceptions.NotFoundException(detail="Order not found", msg_code=MessageCodes.not_found)
    order.tracking_code = tracking_code
    order.status = models.OrderStatus.completed
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def set_product_activation(db: AsyncSession, *, product_id: int, is_active: bool) -> models.Product:
    product = await db.get(models.Product, product_id)
    if not product:
        raise exceptions.NotFoundException(detail="Product not found", msg_code=MessageCodes.not_found)
    product.is_active = is_active
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def set_user_activation(db: AsyncSession, *, user_id: int, is_active: bool) -> models.User:
    user = await db.get(models.User, user_id)
    if not user:
        raise exceptions.NotFoundException(detail="User not found", msg_code=MessageCodes.not_found)
    user.is_active = is_active
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
