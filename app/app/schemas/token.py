from pydantic import BaseModel


class Token(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"


class RefreshToken(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str | None = None
