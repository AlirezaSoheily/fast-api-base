import pytest


@pytest.mark.asyncio
async def test_phone_register_requires_registration_otp(client):
    req_otp = await client.post(
        "/api/v1/auth/register/request-otp",
        json={"phone_number": "+15550000001"},
    )
    assert req_otp.status_code == 200
    register_otp = req_otp.json()["content"]["otp_code"]

    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "phone_number": "+15550000001",
            "otp_code": register_otp,
            "full_name": "Customer",
        },
    )
    assert register_response.status_code == 200


@pytest.mark.asyncio
async def test_phone_otp_login_flow(client):
    otp_response = await client.post(
        "/api/v1/auth/request-otp",
        json={"phone_number": "+15550000001"},
    )
    assert otp_response.status_code == 200
    otp_code = otp_response.json()["content"]["otp_code"]

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"phone_number": "+15550000001", "otp_code": otp_code},
    )
    assert login_response.status_code == 200
    assert login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_admin_category_product_and_order_complete(client, super_user_token):
    category_response = await client.post(
        "/api/v1/admin/categories",
        headers=super_user_token,
        json={"name": "Phones", "slug": "phones"},
    )
    assert category_response.status_code == 200

    product_response = await client.post(
        "/api/v1/admin/products",
        headers=super_user_token,
        json={
            "title": "Admin Product",
            "slug": "admin-product",
            "description": "from admin",
            "category_id": category_response.json()["content"]["id"],
            "brand_id": None,
            "price": 99.5,
            "sku": "ADM-001",
            "stock": 12,
        },
    )
    assert product_response.status_code == 200

    checkout_response = await client.post(
        "/api/v1/checkout",
        json={"session_token": "guest-admin", "shipping_address": "221B Baker Street", "postal_code": "123456"},
        headers=super_user_token,
    )
    assert checkout_response.status_code == 200

    orders_response = await client.get("/api/v1/admin/orders", headers=super_user_token)
    assert orders_response.status_code == 200
    order_id = orders_response.json()["content"][0]["id"]

    complete_response = await client.post(
        f"/api/v1/admin/orders/{order_id}/complete",
        headers=super_user_token,
        json={"tracking_code": "TRACK123456"},
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["content"]["status"] == "completed"


@pytest.mark.asyncio
async def test_admin_activation_endpoints(client, super_user_token):
    product_response = await client.post(
        "/api/v1/admin/products",
        headers=super_user_token,
        json={
            "title": "Toggle Product",
            "slug": "toggle-product",
            "description": "toggle",
            "category_id": None,
            "brand_id": None,
            "price": 12.0,
            "sku": "TOG-001",
            "stock": 2,
        },
    )
    assert product_response.status_code == 200
    product_id = product_response.json()["content"]["id"]

    deactivate_product = await client.patch(
        f"/api/v1/admin/products/{product_id}/activation",
        headers=super_user_token,
        json={"is_active": False},
    )
    assert deactivate_product.status_code == 200
    assert deactivate_product.json()["content"]["is_active"] is False

    deactivate_user = await client.patch(
        "/api/v1/admin/users/1/activation",
        headers=super_user_token,
        json={"is_active": False},
    )
    assert deactivate_user.status_code == 200
    assert deactivate_user.json()["content"]["is_active"] is False

    activate_user = await client.patch(
        "/api/v1/admin/users/1/activation",
        headers=super_user_token,
        json={"is_active": True},
    )
    assert activate_user.status_code == 200
    assert activate_user.json()["content"]["is_active"] is True
