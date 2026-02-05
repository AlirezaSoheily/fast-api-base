from datetime import datetime
from typing import Any, Generic, Sequence, Type, TypeVar, Union

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import Row, RowMapping, and_, exc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app import exceptions
from app.db.base_class import Base
from app.utils import MessageCodes

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get(self, db: AsyncSession, id_: int | str) -> ModelType | None:
        query = select(self.model).where(
            and_(
                self.model.id == id_,
                self.model.is_deleted.is_(None),
            ),
        )
        response = await db.execute(query)
        return response.scalar_one_or_none()

    async def get_by_ids(
        self, db: AsyncSession, list_ids: list[int | str]
    ) -> Sequence[Row | RowMapping | Any]:
        query = select(self.model).where(
            and_(
                self.model.id.in_(list_ids),
                self.model.is_deleted.is_(None),
            )
        )
        response = await db.execute(query)
        return response.scalars().all()

    async def get_count(self, db: AsyncSession) -> int:
        query = select(func.count()).select_from(select(self.model).subquery())
        response = await db.execute(query)
        return response.scalar_one()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        order_field: str = "created",
        order_desc: bool = False,
        order_by: list[Any] | None = None,
    ) -> list[ModelType]:
        if order_by is None:
            order_by = []

        if order_desc:
            order_by.append(getattr(self.model, order_field).desc())
        else:
            order_by.append(getattr(self.model, order_field).asc())

        query = (
            select(self.model)
            .where(self.model.is_deleted.is_(None))
            .order_by(*order_by)
            .offset(skip)
        )

        if limit is not None:
            query = query.limit(limit)

        response = await db.execute(query)
        return response.scalars().all()

    async def get_multi_ordered(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int | None = 100,
        order_by: list = None,
    ) -> Sequence[Row | RowMapping | Any]:
        if order_by is None:
            order_by = []
        order_by.append(self.model.id.asc())

        query = (
            select(self.model)
            .where(self.model.is_deleted.is_(None))
            .order_by(*order_by)
            .offset(skip)
        )
        if limit is None:
            response = await db.execute(query)
            return response.scalars().all()
        response = await db.execute(query.limit(limit))
        return response.scalars().all()

    def make_db_object(
        self, obj_in: CreateSchemaType | UpdateSchemaType | ModelType | dict
    ) -> ModelType:
        if isinstance(obj_in, self.model):
            return obj_in
        elif isinstance(obj_in, BaseModel):
            obj_in = obj_in.model_dump(exclude_none=True)
        return self.model(**obj_in)

    async def create(
        self, db: AsyncSession, obj_in: CreateSchemaType | dict
    ) -> ModelType:
        db_obj = self.make_db_object(obj_in=obj_in)
        try:
            db.add(db_obj)
            await db.commit()
        except exc.IntegrityError:
            await db.rollback()
            raise exceptions.AlreadyExistException(
                detail="Resource already exists",
                msg_code=MessageCodes.already_exist_object,
            )
        except Exception as e:
            await db.rollback()
            raise exceptions.InternalErrorException(
                detail=f"{e}",
                msg_code=MessageCodes.internal_error,
            )

        await db.refresh(db_obj)
        return db_obj

    async def create_multi(
        self, db: AsyncSession, objs_in: list[CreateSchemaType] | list[dict]
    ):
        new_obj_list: list[ModelType] = []
        for obj_in in objs_in:
            db_obj = self.make_db_object(obj_in=obj_in)
            new_obj_list.append(db_obj)
        try:
            db.add_all(new_obj_list)
            await db.commit()
        except exc.IntegrityError:
            await db.rollback()
            raise exceptions.AlreadyExistException(
                detail="Resource already exists",
                msg_code=MessageCodes.already_exist_object,
            )
        except Exception as e:
            await db.rollback()
            raise exceptions.InternalErrorException(
                detail=f"{e}",
                msg_code=MessageCodes.internal_error,
            )

    async def update(
        self,
        db: AsyncSession,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any] | ModelType | None = None,
    ) -> ModelType:
        if obj_in is not None:
            obj_data = jsonable_encoder(db_obj)
            update_data = (
                obj_in
                if isinstance(obj_in, dict)
                else obj_in.model_dump(exclude_unset=True)
            )
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
        if hasattr(self.model, "modified"):
            setattr(db_obj, "modified", datetime.now())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_multi(
        self,
        db: AsyncSession,
        db_objs: list[ModelType],
        objs_in: list[CreateSchemaType] | list[dict],
        refresh: bool = False,
    ) -> list[ModelType] | bool:
        if len(db_objs) != len(objs_in):
            raise ValueError("Length of db_objs and objs_in must match")

        for db_obj, obj_in in zip(db_objs, objs_in):
            obj_data = jsonable_encoder(db_obj)
            update_data = (
                obj_in
                if isinstance(obj_in, dict)
                else obj_in.model_dump(exclude_unset=True)
            )
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
                    if hasattr(db_obj, "modified"):
                        setattr(db_obj, "modified", datetime.now())

        try:
            db.add_all(db_objs)
            await db.commit()

            if refresh:
                for db_obj in db_objs:
                    await db.refresh(db_obj)
                return db_objs

            return True
        except Exception as e:
            await db.rollback()
            raise exceptions.InternalErrorException(
                detail=f"{e}",
                msg_code=MessageCodes.internal_error,
            )

    async def remove(self, db: AsyncSession, id_: int | str) -> ModelType | None:
        query = (
            update(self.model)
            .where(
                and_(
                    self.model.id == id_,
                    self.model.is_deleted.is_(None),
                )
            )
            .values(is_deleted=datetime.now())
            .returning(self.model)
        )
        response = await db.execute(query)
        await db.commit()
        return response.scalar_one_or_none()
