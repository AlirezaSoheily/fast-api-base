from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
import pytest

from app import crud
from app.core.security import verify_password
from app.schemas.user import UserCreate, UserUpdate
from tests.utils.utils import random_email, random_lower_string
from app.models.user import UserRoles, GroupRoles


@pytest.mark.asyncio
class TestUser:
    async def test_create_user(self, db: AsyncSession) -> None:
        username = random_email()
        password = random_lower_string()
        user_in = UserCreate(
            username=username, password=password, roles=[UserRoles.Admin]
        )
        user = await crud.user.create(db, obj_in=user_in)
        assert user.username == username
        assert hasattr(user, "hashed_password")

    async def test_authenticate_user(self, db: AsyncSession) -> None:
        username = random_email()
        password = random_lower_string()
        user_in = UserCreate(
            username=username, password=password, roles=[UserRoles.Admin]
        )
        user = await crud.user.create(db, obj_in=user_in)
        authenticated_user = await crud.user.authenticate(
            db, username=username, password=password
        )
        assert authenticated_user
        assert user.username == authenticated_user.username

    async def test_not_authenticate_user(self, db: AsyncSession) -> None:
        username = random_email()
        password = random_lower_string()
        user = await crud.user.authenticate(db, username=username, password=password)
        assert user is None

    async def test_check_if_user_is_active(self, db: AsyncSession) -> None:
        username = random_email()
        password = random_lower_string()
        user_in = UserCreate(
            username=username, password=password, roles=[UserRoles.Admin]
        )
        user = await crud.user.create(db, obj_in=user_in)
        assert user.is_active is True

    async def test_check_if_user_is_active_inactive(self, db: AsyncSession) -> None:
        username = random_email()
        password = random_lower_string()
        user_in = UserCreate(
            username=username,
            password=password,
            roles=[UserRoles.Admin],
            is_active=True,
        )
        user = await crud.user.create(db, obj_in=user_in)
        assert user.is_active is True

    async def test_check_if_user_is_admin(self, db: AsyncSession) -> None:
        username = random_email()
        password = random_lower_string()
        user_in = UserCreate(
            username=username, password=password, roles=[UserRoles.SuperAdmin]
        )
        user = await crud.user.create(db, obj_in=user_in)
        is_admin = any(role in user.roles for role in GroupRoles.__ADMINS__)
        assert is_admin is True

    async def test_check_if_user_is_admin_normal_user(self, db: AsyncSession) -> None:
        username = random_email()
        password = random_lower_string()
        user_in = UserCreate(
            username=username, password=password, roles=[UserRoles.Consumer]
        )
        user = await crud.user.create(db, obj_in=user_in)
        is_admin = any(role in user.roles for role in GroupRoles.__ADMINS__)
        assert is_admin is False

    async def test_get_user(self, db: AsyncSession) -> None:
        password = random_lower_string()
        username = random_email()
        user_in = UserCreate(
            username=username, password=password, roles=[UserRoles.SuperAdmin]
        )
        user = await crud.user.create(db, obj_in=user_in)
        user_2 = await crud.user.get(db, id_=user.id)
        assert user_2
        assert user.username == user_2.username
        assert jsonable_encoder(user) == jsonable_encoder(user_2)

    async def test_update_user(self, db: AsyncSession) -> None:
        password = random_lower_string()
        username = random_email()
        user_in = UserCreate(
            username=username, password=password, roles=[UserRoles.SuperAdmin]
        )
        user = await crud.user.create(db, obj_in=user_in)
        new_password = random_lower_string()
        user_in_update = UserUpdate(password=new_password, roles=[UserRoles.SuperAdmin])
        await crud.user.update(db, db_obj=user, obj_in=user_in_update)
        user_2 = await crud.user.get(db, id_=user.id)
        assert user_2
        assert user.username == user_2.username
        assert verify_password(new_password, user_2.hashed_password)
