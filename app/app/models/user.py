from sqlalchemy import Boolean, Integer, String, ARRAY
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

import enum


class UserRoles(str, enum.Enum):
    SuperAdmin = "SuperAdmin"
    Admin = "Admin"
    Consumer = "Consumer"


class GroupRoles(list, enum.Enum):
    __ALL__ = [UserRoles.SuperAdmin, UserRoles.Admin, UserRoles.Consumer]
    __ADMINS__ = [
        UserRoles.SuperAdmin,
        UserRoles.Admin,
    ]


class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    full_name: Mapped[str | None] = mapped_column(String)
    username: Mapped[str] = mapped_column(String, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean(), default=True, nullable=False, index=True
    )
    roles: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)),
    )
