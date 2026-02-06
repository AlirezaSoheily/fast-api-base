import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.core.config import settings
from app.models.user import UserRoles

logger = logging.getLogger(__name__)


async def create_super_admin(db: AsyncSession) -> models.User:
    user = await crud.user.get_by_username(db=db, username=settings.FIRST_SUPERADMIN)
    if not user:
        user_in: schemas.UserCreate = schemas.UserCreate(
            username=settings.FIRST_SUPERADMIN,
            password=settings.FIRST_SUPERADMIN_PASSWORD,
            phone_number=settings.FIRST_SUPERADMIN,
            email=settings.FIRST_SUPERADMIN,
            roles=[UserRoles.SuperAdmin],
        )
        user = await crud.user.create(db, obj_in=user_in)
    return user


async def seed_catalog(db: AsyncSession) -> None:
    exists = (await db.execute(select(models.Product).limit(1))).scalar_one_or_none()
    if exists:
        return
    brand = models.Brand(name="Acme", slug="acme")
    category = models.Category(name="General", slug="general")
    db.add_all([brand, category])
    await db.flush()
    for idx in range(1, 31):
        product = models.Product(
            title=f"Sample Product {idx}",
            slug=f"sample-product-{idx}",
            description="Seeded sample product",
            brand_id=brand.id,
            category_id=category.id,
            is_active=True,
        )
        db.add(product)
        await db.flush()
        db.add(
            models.ProductVariant(
                product_id=product.id,
                sku=f"SKU-{idx:03d}",
                price=10 + idx,
                stock=50,
            )
        )
    await db.commit()


async def init_db(db: AsyncSession) -> None:
    await create_super_admin(db)
    if settings.DEBUG:
        await seed_catalog(db)
