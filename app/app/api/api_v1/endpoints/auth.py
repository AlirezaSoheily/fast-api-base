from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app import exceptions as exc
from app import models, schemas
from app.api import deps
from app.api.api_v1 import services
from app.api.api_v1.endpoints.users import namespace as users_namespace
from app.utils import APIResponse, APIResponseType
from app.utils.message_codes import MessageCodes
from app.models.user import GroupRoles
from app.utils.user_role import allowed_roles
from cache import invalidate

router = APIRouter()


@router.post("/login")
async def login(
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> schemas.Token:
    """Return Access Token to output"""
    user_in = schemas.LoginUser(
        username=form_data.username, password=form_data.password
    )
    tokens = await services.login(db=db, user_in=user_in)
    return tokens


@router.post("/register")
@invalidate(namespace=users_namespace)
@allowed_roles(GroupRoles.__ADMINS__)
async def register(
    user_in: schemas.UserCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: schemas.User = Depends(deps.check_user_role),
) -> APIResponseType[schemas.User]:
    """Register new user"""
    response = await services.register(db=db, user_in=user_in)
    return APIResponse(response)


@router.get("/me")
@allowed_roles(GroupRoles.__ALL__)
async def me(
    current_user: models.User = Depends(deps.check_user_role),
) -> APIResponseType[schemas.User]:
    """Retrieve current user"""
    return APIResponse(current_user)


@router.get("/logout")
@allowed_roles(GroupRoles.__ALL__)
async def logout(
    request: Request,
    current_user: schemas.User = Depends(deps.check_user_role),
    cache: Redis = Depends(deps.get_redis),
) -> APIResponseType[schemas.Msg]:
    auth = request.headers.get("Authorization")
    """Logout from system"""
    if auth is None:
        raise exc.UnauthorizedException(
            detail="Not authenticated", msg_code=MessageCodes.not_authorized
        )

    await services.logout(
        authorization_header=auth,
        cache=cache,
    )
    return APIResponse(schemas.Msg(msg="You have successfully logged out"))
