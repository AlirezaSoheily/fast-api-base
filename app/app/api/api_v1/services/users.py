from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app import exceptions as exc
from app import models, schemas
from app.utils import MessageCodes
from app.models.user import GroupRoles


async def read_user_by_id(
    user_id: int,
    current_user: models.User,
    db: AsyncSession,
) -> schemas.User:
    user = await crud.user.get(db, id_=user_id)
    if not user:
        raise exc.NotFoundException(
            detail="User not found",
            msg_code=MessageCodes.not_found,
        )
    return user


async def update_user(
    user_id: int,
    user_in: schemas.UserUpdate,
    db: AsyncSession,
    current_user: models.User,
) -> schemas.User:
    user = await crud.user.get(db, id_=user_id)
    if not user:
        raise exc.NotFoundException(
            detail="The user with this username does not exist",
            msg_code=MessageCodes.not_found,
        )
    user = await crud.user.update(
        db, db_obj=user, obj_in=user_in.model_dump(exclude_none=True)
    )
    return user
