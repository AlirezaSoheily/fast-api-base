import time

from redis.asyncio import client
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas, utils
from app import exceptions as exc
from app.core.config import ACCESS_TOKEN_BLACKLIST_KEY
from app.core.security import JWTHandler


async def register(db: AsyncSession, user_in: schemas.UserCreate) -> schemas.User:
    user = await crud.user.get_by_username(db=db, username=user_in.username)
    if user:
        raise exc.AlreadyExistException(
            detail="The user with this username already exists",
            msg_code=utils.MessageCodes.bad_request,
        )
    user = await crud.user.create(db=db, obj_in=user_in)
    return user


async def login(db: AsyncSession, user_in: schemas.LoginUser) -> schemas.Token:
    user = await crud.user.authenticate(
        db=db, username=user_in.username, password=user_in.password
    )
    if not user:
        raise exc.NotFoundException(
            detail="Incorrect username or password",
            msg_code=utils.MessageCodes.incorrect_username_or_password,
        )
    elif not crud.user.is_active(user):
        raise exc.ForbiddenException(
            detail="The user account is not activated.",
            msg_code=utils.MessageCodes.inactive_user,
            msg_code_params=[user.username],
        )
    access_token = JWTHandler.encode(payload={"sub": "access", "id": str(user.id)})

    return schemas.Token(access_token=access_token, token_type="bearer")


async def logout(authorization_header: str, cache: client.Redis):
    if not cache:
        raise exc.InternalErrorException(
            detail="Redis connection is not initialized",
            msg_code=utils.MessageCodes.internal_error,
        )

    access_token = JWTHandler.get_access_token(authorization_header)

    if JWTHandler.verify_token(access_token):
        access_token_key = ACCESS_TOKEN_BLACKLIST_KEY.format(token=access_token)
        await cache.set(
            access_token_key,
            time.time(),  # Store current timestamp
            ex=JWTHandler.token_expiration(access_token),
        )
    else:
        raise exc.UnauthorizedException(
            detail="Invalid or expired token",
            msg_code=utils.MessageCodes.invalid_token,
        )
