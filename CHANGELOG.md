# Changelog

## 2026-02-06
- `init_db` now seeds catalog data only when `DEBUG=True` in environment.
- Added admin activation endpoints to activate/deactivate products and users.
- Checkout still requires `shipping_address` and `postal_code` and stores them on the order.
