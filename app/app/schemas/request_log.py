from datetime import datetime
from typing import Optional

import pytz
from pydantic import BaseModel, ConfigDict, field_serializer

from app.models.request_log import RequestLogType
from app.core.config import settings


class RequestLogInDBBase(BaseModel):
    id: int
    created: datetime
    modified: datetime
    model_config = ConfigDict(from_attributes=True)


class RequestLogCreate(BaseModel):
    request: Optional[str] = None
    response: Optional[str] = None
    service_name: Optional[str] = None
    method: Optional[str] = None
    user_id: Optional[int] = None
    status_code: Optional[int] = None
    ip: Optional[str] = None
    trace: Optional[str] = None
    processing_time: Optional[float] = None
    tracker_id: Optional[str] = None
    type: RequestLogType
    start_processing_at: Optional[datetime] = None


class RequestLogUpdate(BaseModel):
    pass


class RequestLog(BaseModel):
    id: int
    service_name: str
    created: datetime

    request: str | None
    response: str | None
    method: str | None
    user_id: int | None
    status_code: int | None
    ip: str | None
    trace: str | None
    processing_time: float | None
    tracker_id: str | None
    type: RequestLogType
    start_processing_at: datetime | None

    @field_serializer("created", "start_processing_at")
    def set_timezone(self, v: datetime) -> datetime:
        if type(v) == datetime and str(v.tzinfo) == str(pytz.utc):
            v = v.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(settings.TZ))
        return v
