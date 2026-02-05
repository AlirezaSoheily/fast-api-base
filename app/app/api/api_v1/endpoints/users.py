from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.api.api_v1 import services
from app.log import log
from app.utils import APIResponse, APIResponseType
from app.models.user import GroupRoles
from app.utils.user_role import allowed_roles
from cache import cache, invalidate
from cache.util import ONE_DAY_IN_SECONDS

router = APIRouter(route_class=log.LogRoute)
namespace = "user"


@router.get("/")
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
@allowed_roles(GroupRoles.__ADMINS__)
async def read_users(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.check_user_role),
) -> APIResponseType[list[schemas.User]]:
    """
    Retrieve users.
    """
    users = await crud.user.get_multi(db, skip=skip, limit=limit)
    return APIResponse(users)


@router.get("/{user_id}")
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
@allowed_roles(GroupRoles.__ADMINS__)
async def read_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.check_user_role),
) -> APIResponseType[schemas.User]:
    """
    Get a specific user by id.
    """
    response = await services.read_user_by_id(
        db=db, user_id=user_id, current_user=current_user
    )
    return APIResponse(response)


@router.put("/{user_id}")
@invalidate(namespace=namespace)
@allowed_roles(GroupRoles.__ADMINS__)
async def update_user(
    user_id: int,
    user_in: schemas.UserUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.check_user_role),
) -> APIResponseType[schemas.User]:
    """
    Update a user.
    """
    response = await services.update_user(
        db=db, user_id=user_id, user_in=user_in, current_user=current_user
    )
    return APIResponse(response)
