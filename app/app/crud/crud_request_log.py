from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder

from app.crud.base import CRUDBase
from app.models.request_log import RequestLog
from app.schemas.request_log import RequestLogCreate, RequestLogUpdate


class CRUDRequestLog(CRUDBase[RequestLog, RequestLogCreate, RequestLogUpdate]):
    async def create(
        self, db: AsyncSession, obj_in: dict[Any, Any] | RequestLogCreate | Any
    ) -> RequestLog:
        if isinstance(obj_in, BaseModel):
            obj_in = obj_in.model_dump()
        if not isinstance(obj_in, dict):
            obj_in = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in)  # type: ignore
        db.add(db_obj)
        await db.commit()
        return db_obj

    async def get_by_tracker_id(
        self, db: AsyncSession, tracker_id: int | str
    ) -> RequestLog | None:
        query = select(self.model).where(
            and_(
                self.model.tracker_id == tracker_id,
                self.model.is_deleted.is_(None),
            ),
        )
        response = await db.execute(query)
        return response.scalar_one_or_none()


request_log = CRUDRequestLog(RequestLog)
