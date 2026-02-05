import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.core.config import settings
from app.models.user import UserRoles

logger = logging.getLogger(__name__)


async def create_super_admin(db: AsyncSession) -> None:
    user = await crud.user.get_by_username(db=db, username=settings.FIRST_SUPERADMIN)
    if not user:
        user_in: schemas.UserCreate = schemas.UserCreate(
            username=settings.FIRST_SUPERADMIN,
            password=settings.FIRST_SUPERADMIN_PASSWORD,
            roles=[UserRoles.SuperAdmin],
        )
        user = await crud.user.create(db, obj_in=user_in)


async def init_db(db: AsyncSession) -> None:
    await create_super_admin(db)
