import logging
import secrets
from typing import Annotated, AsyncGenerator, NewType
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as redis
from fastapi import Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
from redis.asyncio import client

from app import crud, exceptions, models, utils
from app.core.config import ACCESS_TOKEN_BLACKLIST_KEY, AuthMethod, settings
from app.core.security import JWTHandler, basic_security
from app.db.session import async_session
from app.utils import redis_client
from app.utils.user_role import check_allowed_roles

logger = logging.getLogger(__name__)
UserId = NewType("UserId", int)


class OAuth2(OAuth2PasswordBearer):
    async def __call__(self, request: Request):
        authorization = request.headers.get("Authorization", "").lower()
        if "bearer" not in authorization:
            return None
        if AuthMethod.JWT not in settings.ALLOWED_AUTH_METHODS:
            raise exceptions.UnauthorizedException(
                msg_code=utils.MessageCodes.expired_token,
            )
        return await super().__call__(request)


class BasicAuth(HTTPBasic):
    async def __call__(self, request: Request):
        authorization = request.headers.get("Authorization", "").lower()
        if "basic" not in authorization:
            return None
        if AuthMethod.BASIC not in settings.ALLOWED_AUTH_METHODS:
            raise exceptions.UnauthorizedException(
                msg_code=utils.MessageCodes.expired_token,
            )
        return await super().__call__(request)


reusable_oauth2 = OAuth2(
    tokenUrl=f"{settings.SUB_PATH}{settings.API_V1_STR}/auth/login"
)


async def get_db() -> AsyncGenerator:
    """
    Dependency function for get database
    """
    async with async_session() as session:
        yield session


async def get_redis() -> client.Redis:
    """
    Dependency function that get redis client
    """

    try:
        if await redis_client.ping():
            return redis_client
        raise redis.RedisError("ping error")

    except Exception as e:
        logger.error(f"Redis connection failed\n{e}")
        raise


async def get_user_id_from_access_token(
    request: Request,
    access_token: str = Depends(reusable_oauth2),
    cache: client.Redis = Depends(get_redis),
) -> int:
    token = JWTHandler.decode(access_token)
    if await cache.get(ACCESS_TOKEN_BLACKLIST_KEY.format(token=access_token)):
        raise exceptions.UnauthorizedException(
            msg_code=utils.MessageCodes.expired_token,
        )

    user_id = token.get("id")

    if token.get("sub") != "access" or not user_id:
        raise exceptions.UnauthorizedException(
            msg_code=utils.MessageCodes.invalid_token
        )
    request.state.user_id = user_id
    return int(user_id)


def _check_basic_credentials(
    credentials: Annotated[HTTPBasicCredentials, Depends(basic_security)],
) -> HTTPBasicCredentials:
    if not credentials or not credentials.username or not credentials.password:
        raise exceptions.UnauthorizedException(
            msg_code=utils.MessageCodes.not_authorized,
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials


def health_user(
    credentials: HTTPBasicCredentials = Depends(_check_basic_credentials),
) -> str:
    if not (
        secrets.compare_digest(
            credentials.username.encode("utf8"), settings.HEALTH_USERNAME.encode("utf8")
        )
        and secrets.compare_digest(
            credentials.password.encode("utf8"), settings.HEALTH_PASSWORD.encode("utf8")
        )
    ):
        raise exceptions.UnauthorizedException(
            msg_code=utils.MessageCodes.incorrect_username_or_password,
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


# await crud.user.get(db=db, id_=current_user_id)


async def get_current_user_from_basic(
    db: AsyncSession = Depends(get_db),
    *,
    request: Request,
    credentials: HTTPBasicCredentials = Depends(_check_basic_credentials),
) -> models.User:
    current_user = await crud.user.authenticate(
        db=db, username=credentials.username, password=credentials.password
    )
    return current_user


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    *,
    request: Request,
    access_token: str = Depends(reusable_oauth2),
    credentials: HTTPBasicCredentials = Depends(basic_security),
    cache: client.Redis = Depends(get_redis),
) -> models.User:
    current_user = None
    if access_token:
        try:
            user_id = await get_user_id_from_access_token(
                access_token=access_token, cache=cache, request=request
            )
            current_user = await crud.user.get(db=db, id_=user_id)

        except Exception as e:
            raise exceptions.UnauthorizedException(
                msg_code=utils.MessageCodes.invalid_token, detail="Invalid token"
            ) from e

    if not current_user and credentials:
        try:
            credentials = _check_basic_credentials(credentials=credentials)
            current_user = await get_current_user_from_basic(
                db, credentials=credentials, request=request
            )
        except exceptions.UnauthorizedException as e:
            logger.error(f"Basic auth error: {str(e)}")
            raise exceptions.UnauthorizedException(
                msg_code=utils.MessageCodes.incorrect_username_or_password,
                headers={"WWW-Authenticate": "Basic"},
            ) from e

    if not current_user or not crud.user.is_active(current_user):
        raise exceptions.UnauthorizedException(
            msg_code=utils.MessageCodes.not_authorized,
        )
    request.state.user_id = current_user.id_
    return current_user


def check_user_role(
    request: Request,
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    is_allowed: bool = check_allowed_roles(request, user_roles=current_user.roles)
    if is_allowed:
        return current_user

    raise exceptions.ForbiddenException(detail="permission denied")
