"""Ecommerce API endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.api import deps
from app.api.api_v1.services import ecommerce as svc
from app.models.user import GroupRoles
from app.schemas import Token
from app.schemas.ecommerce import (
    ActivationRequest,
    AdminOrderCompleteRequest,
    CartAddRequest,
    CartItemOut,
    CartOut,
    CategoryCreate,
    CheckoutRequest,
    CheckoutResponse,
    OrderOut,
    OtpLoginRequest,
    OtpRequest,
    PaymentWebhookPayload,
    ProductCreate,
    ProductFilter,
    ProductOut,
    RefreshRequest,
    RegisterOtpRequest,
    RegisterRequest,
)
from app.utils import APIResponse, APIResponseType
from app.utils.user_role import allowed_roles

router = APIRouter()


@router.post("/auth/register/request-otp")
async def register_request_otp(
    payload: RegisterOtpRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> APIResponseType[dict]:
    otp_code = await svc.request_register_otp(db, payload.phone_number)
    # TODO: replace with SMS provider integration in production.
    return APIResponse({"sent": True, "otp_code": otp_code})


@router.post("/auth/register")
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> APIResponseType[dict]:
    user = await svc.register_user(
        db,
        phone_number=payload.phone_number,
        otp_code=payload.otp_code,
        full_name=payload.full_name,
        email=payload.email,
    )
    return APIResponse({"user_id": user.id, "phone_number": user.phone_number})


@router.post("/auth/request-otp")
async def request_otp(
    payload: OtpRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> APIResponseType[dict]:
    otp_code = await svc.request_login_otp(db, payload.phone_number)
    # TODO: replace with SMS provider integration in production.
    return APIResponse({"sent": True, "otp_code": otp_code})


@router.post("/auth/login")
async def login(
    payload: OtpLoginRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> Token:
    access, refresh = await svc.login_with_otp(
        db,
        phone_number=payload.phone_number,
        otp_code=payload.otp_code,
    )
    return Token(access_token=access, refresh_token=refresh)


@router.post("/auth/refresh")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(deps.get_db)) -> Token:
    access, refresh_token = await svc.refresh_access_token(db, payload.refresh_token)
    return Token(access_token=access, refresh_token=refresh_token)


@router.get("/products")
async def products(
    search: str | None = None,
    category_id: int | None = None,
    brand_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(deps.get_db),
) -> APIResponseType[list[ProductOut]]:
    rows = await svc.list_products(
        db,
        ProductFilter(
            search=search,
            category_id=category_id,
            brand_id=brand_id,
            min_price=min_price,
            max_price=max_price,
            page=page,
            size=size,
        ),
    )
    return APIResponse([ProductOut.model_validate(item) for item in rows])


@router.post("/cart/add")
async def add_to_cart(
    payload: CartAddRequest,
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
) -> APIResponseType[dict]:
    user_id = getattr(request.state, "user_id", None)
    await svc.add_to_cart(
        db,
        user_id=user_id,
        session_token=payload.session_token,
        variant_id=payload.variant_id,
        quantity=payload.quantity,
    )
    return APIResponse({"added": True})


@router.get("/cart")
async def get_cart(
    request: Request,
    session_token: str | None = None,
    db: AsyncSession = Depends(deps.get_db),
) -> APIResponseType[CartOut]:
    user_id = getattr(request.state, "user_id", None)
    items, total = await svc.get_cart(db, user_id=user_id, session_token=session_token)
    parsed = [
        CartItemOut(
            variant_id=variant.id,
            quantity=item.quantity,
            unit_price=float(variant.price),
        )
        for item, variant in items
    ]
    return APIResponse(CartOut(items=parsed, total_amount=float(total)))


@router.post("/checkout")
async def checkout(
    payload: CheckoutRequest,
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
) -> APIResponseType[CheckoutResponse]:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        user_id = 1
    order, payment = await svc.checkout(
        db,
        user_id=user_id,
        session_token=payload.session_token,
        shipping_address=payload.shipping_address,
        postal_code=payload.postal_code,
    )
    return APIResponse(
        CheckoutResponse(order_id=order.id, payment_url=f"/sandbox/pay/{payment.provider_ref}")
    )


@router.get("/orders/me")
async def my_orders(
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
) -> APIResponseType[list[OrderOut]]:
    user_id = getattr(request.state, "user_id", 1)
    rows = (await db.execute(select(models.Order).where(models.Order.user_id == user_id))).scalars().all()
    return APIResponse([OrderOut.model_validate(row) for row in rows])


@router.post("/payments/webhook")
async def payment_webhook(
    payload: PaymentWebhookPayload,
    db: AsyncSession = Depends(deps.get_db),
) -> APIResponseType[dict]:
    payment = (
        await db.execute(select(models.Payment).where(models.Payment.provider_ref == payload.provider_ref))
    ).scalar_one_or_none()
    if payment:
        payment.status = payload.status
        if payload.status.value == "succeeded":
            order = await db.get(models.Order, payment.order_id)
            if order:
                order.status = models.OrderStatus.paid
                db.add(order)
        db.add(payment)
        await db.commit()
    return APIResponse({"ok": True})


@router.post("/admin/categories")
@allowed_roles(GroupRoles.__ADMINS__)
async def admin_create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.check_user_role),
) -> APIResponseType[dict]:
    category = await svc.create_category(
        db,
        name=payload.name,
        slug=payload.slug,
        parent_id=payload.parent_id,
    )
    return APIResponse({"id": category.id, "name": category.name})


@router.post("/admin/products")
@allowed_roles(GroupRoles.__ADMINS__)
async def admin_create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.check_user_role),
) -> APIResponseType[dict]:
    product = await svc.create_product(
        db,
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        brand_id=payload.brand_id,
        category_id=payload.category_id,
        price=payload.price,
        sku=payload.sku,
        stock=payload.stock,
    )
    return APIResponse({"id": product.id, "slug": product.slug})


@router.get("/admin/orders")
@allowed_roles(GroupRoles.__ADMINS__)
async def admin_orders(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.check_user_role),
) -> APIResponseType[list[OrderOut]]:
    rows = await svc.list_orders(db)
    return APIResponse([OrderOut.model_validate(row) for row in rows])


@router.post("/admin/orders/{order_id}/complete")
@allowed_roles(GroupRoles.__ADMINS__)
async def admin_complete_order(
    order_id: int,
    payload: AdminOrderCompleteRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.check_user_role),
) -> APIResponseType[OrderOut]:
    order = await svc.complete_order(db, order_id=order_id, tracking_code=payload.tracking_code)
    return APIResponse(OrderOut.model_validate(order))


@router.patch("/admin/products/{product_id}/activation")
@allowed_roles(GroupRoles.__ADMINS__)
async def admin_set_product_activation(
    product_id: int,
    payload: ActivationRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.check_user_role),
) -> APIResponseType[dict]:
    product = await svc.set_product_activation(db, product_id=product_id, is_active=payload.is_active)
    return APIResponse({"id": product.id, "is_active": product.is_active})


@router.patch("/admin/users/{user_id}/activation")
@allowed_roles(GroupRoles.__ADMINS__)
async def admin_set_user_activation(
    user_id: int,
    payload: ActivationRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.check_user_role),
) -> APIResponseType[dict]:
    user = await svc.set_user_activation(db, user_id=user_id, is_active=payload.is_active)
    return APIResponse({"id": user.id, "is_active": user.is_active})
