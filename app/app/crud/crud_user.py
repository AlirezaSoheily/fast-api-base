from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        query = select(self.model).where(
            and_(
                self.model.username == username,
                self.model.is_deleted.is_(None),
            )
        )
        response = await db.execute(query)
        return response.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: UserCreate | dict) -> User:
        if isinstance(obj_in, dict):
            password = obj_in["password"]
        else:
            password = obj_in.password

        obj_in_data = jsonable_encoder(obj_in)
        obj_in_data["hashed_password"] = get_password_hash(password)
        del obj_in_data["password"]
        obj_in_data = {k: v for k, v in obj_in_data.items() if v is not None}
        return await super().create(db, obj_in=obj_in_data)

    async def create_multi(
        self, db: AsyncSession, objs_in: list[UserCreate] | list[dict]
    ) -> User:

        new_objs_in_list = []
        for obj_in in objs_in:
            hashed_password = (
                get_password_hash(obj_in["password"])
                if isinstance(obj_in, dict)
                else get_password_hash(obj_in.password)
            )

            obj_in_data = jsonable_encoder(obj_in)
            obj_in_data["hashed_password"] = hashed_password
            del obj_in_data["password"]
            obj_in_data = {k: v for k, v in obj_in_data.items() if v is not None}
            new_objs_in_list.append(obj_in_data)

        return await super().create_multi(db, objs_in=new_objs_in_list)

    async def update(
        self,
        db: AsyncSession,
        db_obj: User,
        obj_in: UserUpdate | dict[str, Any] | None = None,
    ) -> User:
        if obj_in is not None:
            if isinstance(obj_in, dict):
                update_data = obj_in

            else:
                update_data = obj_in.model_dump(exclude_none=True)
            if "password" in update_data and update_data["password"]:
                hashed_password = get_password_hash(update_data["password"])
                del update_data["password"]
                update_data["hashed_password"] = hashed_password
        else:
            update_data = None
        return await super().update(db=db, db_obj=db_obj, obj_in=update_data)

    async def update_multi(
        self,
        db: AsyncSession,
        db_objs: list[User],
        objs_in: list[UserUpdate] | list[dict[str, Any]],
        refresh: bool = False,
    ) -> list[User] | bool:

        new_objs_in_list = []
        for obj_in in objs_in:
            if isinstance(obj_in, UserUpdate):
                update_data = obj_in.model_dump(exclude_unset=True)
            else:
                update_data = obj_in

            if "password" in update_data and update_data["password"]:
                hashed_password = get_password_hash(update_data["password"])
                del update_data["password"]
                update_data["hashed_password"] = hashed_password

            new_objs_in_list.append(update_data)

        return await super().update_multi(
            db=db, db_objs=db_objs, objs_in=new_objs_in_list, refresh=refresh
        )

    async def authenticate(
        self, db: AsyncSession, username: str, password: str
    ) -> User | None:
        user_obj = await self.get_by_username(db, username=username)
        if not user_obj:
            return None
        if not verify_password(password, user_obj.hashed_password):
            return None
        return user_obj

    def is_active(self, user: User) -> bool:
        return user.is_active


user = CRUDUser(User)
