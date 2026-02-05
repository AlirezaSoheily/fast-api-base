from pydantic import BaseModel, ConfigDict

from app.models.user import UserRoles


class UserBase(BaseModel):
    username: str | None = None
    full_name: str | None = None
    is_active: bool = True
    roles: list[UserRoles] | None = None


class UserCreate(UserBase):
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: str | None = None


class UserInDBBase(UserBase):
    id: int | None = None
    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str


class UserIn(BaseModel):
    username: str
    password: str


class LoginUser(BaseModel):
    username: str
    password: str
