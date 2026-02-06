# fast-api-base Ecommerce Backend

Production-oriented FastAPI backend for ecommerce workloads (OTP auth, catalog, cart, checkout, payments, inventory-aware order creation), built on SQLAlchemy + Alembic + Redis + Celery.

## Quickstart

```bash
docker-compose up --build
```

API: `http://localhost:8000`  
OpenAPI docs: `http://localhost:8000/docs`

## Migrations

```bash
cd app
make migrate
```

## Seed data

```bash
cd app
make seed
```

## Tests

```bash
cd app
python -m pytest
```

## Main API flows

```bash
# request registration otp
curl -X POST http://localhost:8000/api/v1/auth/register/request-otp -H 'Content-Type: application/json' -d '{"phone_number":"+15550000001"}'

# register with received otp
curl -X POST http://localhost:8000/api/v1/auth/register -H 'Content-Type: application/json' -d '{"phone_number":"+15550000001","otp_code":"123456","full_name":"John"}'

# request login otp
curl -X POST http://localhost:8000/api/v1/auth/request-otp -H 'Content-Type: application/json' -d '{"phone_number":"+15550000001"}'

# login with otp
curl -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"phone_number":"+15550000001","otp_code":"123456"}'

# product listing
curl http://localhost:8000/api/v1/products

# admin: create category
curl -X POST http://localhost:8000/api/v1/admin/categories -H 'Authorization: Bearer <ADMIN_ACCESS_TOKEN>' -H 'Content-Type: application/json' -d '{"name":"Phones","slug":"phones"}'

# admin: complete order
curl -X POST http://localhost:8000/api/v1/admin/orders/1/complete -H 'Authorization: Bearer <ADMIN_ACCESS_TOKEN>' -H 'Content-Type: application/json' -d '{"tracking_code":"TRACK123"}'
```

# checkout (shipping address + postal code are required)
curl -X POST http://localhost:8000/api/v1/checkout -H 'Content-Type: application/json' -d '{"session_token":"guest-1","shipping_address":"221B Baker Street","postal_code":"123456"}'


# admin: deactivate product
curl -X PATCH http://localhost:8000/api/v1/admin/products/1/activation -H 'Authorization: Bearer <ADMIN_ACCESS_TOKEN>' -H 'Content-Type: application/json' -d '{"is_active":false}'

# admin: deactivate user
curl -X PATCH http://localhost:8000/api/v1/admin/users/2/activation -H 'Authorization: Bearer <ADMIN_ACCESS_TOKEN>' -H 'Content-Type: application/json' -d '{"is_active":false}'
