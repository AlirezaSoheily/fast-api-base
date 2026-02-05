import enum
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class RequestLogType(enum.StrEnum):
    Incoming = "Incoming"
    Outgoing = "Outgoing"
    AutomationOutgoing = "AutomationOutgoing"


class RequestLog(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int | None] = mapped_column(Integer)
    method: Mapped[str | None] = mapped_column(String(10))
    service_name: Mapped[str | None] = mapped_column(Text)
    processing_time: Mapped[float | None] = mapped_column(Float)
    status_code: Mapped[int | None] = mapped_column(Integer)
    tracker_id: Mapped[str | None] = mapped_column(String(100))
    ip: Mapped[str | None] = mapped_column(String(50))
    request: Mapped[str | None] = mapped_column(Text)
    response: Mapped[str | None] = mapped_column(Text)
    trace: Mapped[str | None] = mapped_column(Text, default="")
    type: Mapped[RequestLogType] = mapped_column(Text)
    start_processing_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )

    def __str__(self):
        return f"{self.method=},{self.service_name=},{self.user_id=},{self.ip=},{self.tracker_id=}"
