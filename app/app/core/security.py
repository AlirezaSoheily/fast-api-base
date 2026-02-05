from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any

import jwt
from fastapi.security import HTTPBasic

from app import exceptions
from app.core.config import settings
from app.utils import MessageCodes

basic_security = HTTPBasic(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashed_password == sha256(plain_password.encode()).hexdigest()


def get_password_hash(password: str) -> str:
    return sha256(password.encode()).hexdigest()


class JWTHandler:
    secret_key = settings.SECRET_KEY
    algorithm = settings.JWT_ALGORITHM
    access_token_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    refresh_token_expire = settings.REFRESH_TOKEN_EXPIRE_MINUTES

    @staticmethod
    def encode(payload: dict[str, Any]) -> str:
        expire = datetime.now() + timedelta(minutes=JWTHandler.access_token_expire)
        payload.update({"exp": expire.timestamp()})
        return jwt.encode(
            payload, JWTHandler.secret_key, algorithm=JWTHandler.algorithm
        )

    @staticmethod
    def decode(token: str) -> dict:
        try:
            result: dict = jwt.decode(
                token, JWTHandler.secret_key, algorithms=[JWTHandler.algorithm]
            )
            return result
        except jwt.ExpiredSignatureError as exc:
            raise exceptions.UnauthorizedException(
                detail="Token expired",
                msg_code=MessageCodes.expired_token,
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise exceptions.UnauthorizedException(
                detail="Invalid token",
                msg_code=MessageCodes.invalid_token,
            ) from exc

    @staticmethod
    def decode_expired(token: str) -> dict:
        try:
            return jwt.decode(
                token,
                JWTHandler.secret_key,
                algorithms=[JWTHandler.algorithm],
                options={"verify_exp": False},
            )
        except jwt.InvalidTokenError as exc:
            raise exceptions.UnauthorizedException(
                detail="Invalid token",
                msg_code=MessageCodes.invalid_token,
            ) from exc

    @staticmethod
    def token_expiration(token: str) -> timedelta | None:
        try:
            decoded_token = jwt.decode(
                token,
                JWTHandler.secret_key,
                algorithms=[JWTHandler.algorithm],
                options={"verify_exp": True},
            )
            exp = int(decoded_token.get("exp"))
            if not exp:
                raise exceptions.UnauthorizedException(
                    detail="Invalid token exp",
                    msg_code=MessageCodes.invalid_token,
                )
            return datetime.fromtimestamp(exp) - datetime.now()
        except jwt.ExpiredSignatureError as exc:
            raise exceptions.UnauthorizedException(
                detail="Token expired",
                msg_code=MessageCodes.expired_token,
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise exceptions.UnauthorizedException(
                detail="Invalid token",
                msg_code=MessageCodes.invalid_token,
            ) from exc

    @staticmethod
    def get_access_token(authorization_header: str) -> str:
        if not authorization_header or not authorization_header.startswith("Bearer "):
            raise exceptions.UnauthorizedException(
                detail="Authorization header is missing",
                msg_code=MessageCodes.not_authorized,
            )

        # Extract the access token
        access_token = authorization_header.split(" ")[1]
        return access_token

    @staticmethod
    def verify_token(token: str) -> bool:
        """Verify the token without raising exceptions."""
        try:
            jwt.decode(token, JWTHandler.secret_key, algorithms=[JWTHandler.algorithm])
            return True
        except jwt.ExpiredSignatureError:
            return False  # Token is expired
        except jwt.InvalidTokenError:
            return False  # Token is invalid
