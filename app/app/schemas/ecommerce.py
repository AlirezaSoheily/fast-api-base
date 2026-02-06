"""Schemas for ecommerce API resources."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.ecommerce import OrderStatus, PaymentStatus


class RegisterOtpRequest(BaseModel):
    phone_number: str = Field(min_length=8, max_length=20)


class RegisterRequest(BaseModel):
    phone_number: str = Field(min_length=8, max_length=20)
    otp_code: str = Field(min_length=4, max_length=8)
    full_name: str | None = None
    email: EmailStr | None = None


class OtpRequest(BaseModel):
    phone_number: str = Field(min_length=8, max_length=20)


class OtpLoginRequest(BaseModel):
    phone_number: str = Field(min_length=8, max_length=20)
    otp_code: str = Field(min_length=4, max_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str


class CategoryCreate(BaseModel):
    name: str
    slug: str
    parent_id: int | None = None


class ProductCreate(BaseModel):
    title: str
    slug: str
    description: str | None = None
    brand_id: int | None = None
    category_id: int | None = None
    price: float = Field(gt=0)
    sku: str
    stock: int = Field(ge=0)


class AdminOrderCompleteRequest(BaseModel):
    tracking_code: str = Field(min_length=3, max_length=120)


class ActivationRequest(BaseModel):
    is_active: bool


class ProductFilter(BaseModel):
    search: str | None = None
    category_id: int | None = None
    brand_id: int | None = None
    min_price: float | None = None
    max_price: float | None = None
    page: int = 1
    size: int = 20


class ProductVariantOut(BaseModel):
    id: int
    sku: str
    color: str | None
    size: str | None
    price: float
    stock: int
    model_config = ConfigDict(from_attributes=True)


class ProductOut(BaseModel):
    id: int
    title: str
    slug: str
    description: str | None
    variants: list[ProductVariantOut]
    model_config = ConfigDict(from_attributes=True)


class CartAddRequest(BaseModel):
    variant_id: int
    quantity: int = Field(gt=0)
    session_token: str | None = None


class CartItemOut(BaseModel):
    variant_id: int
    quantity: int
    unit_price: float


class CartOut(BaseModel):
    items: list[CartItemOut]
    total_amount: float


class CheckoutRequest(BaseModel):
    session_token: str | None = None
    shipping_address: str = Field(min_length=5, max_length=500)
    postal_code: str = Field(min_length=3, max_length=20)


class CheckoutResponse(BaseModel):
    order_id: int
    payment_url: str


class OrderOut(BaseModel):
    id: int
    status: OrderStatus
    total_amount: float
    tracking_code: str | None = None
    shipping_address: str
    postal_code: str
    model_config = ConfigDict(from_attributes=True)


class PaymentWebhookPayload(BaseModel):
    provider_ref: str
    status: PaymentStatus
