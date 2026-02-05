from datetime import datetime
from typing import Any

# from persiantools.jdatetime import JalaliDate
import jdatetime
from sqlalchemy import DateTime, MetaData
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )
    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    is_deleted: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now, index=True
    )
    modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        index=True,
        onupdate=datetime.now,
    )

    def __str__(self):
        return f"{self.__tablename__}:{self.id}"

    def __repr__(self):
        try:
            return f"{self.__class__.__name__}({self.__tablename__}:{self.id})"
        except:
            return f"Faulty-{self.__class__.__name__}"

    @property
    def created_jalali(self) -> str:
        created = self.created.replace(tzinfo=None)
        utc = datetime.strptime(str(created), "%Y-%m-%d %H:%M:%S.%f")
        jalali_date = jdatetime.datetime.fromgregorian(datetime=utc)
        return jalali_date.strftime("%Y-%m-%d %H:%M:%S")
