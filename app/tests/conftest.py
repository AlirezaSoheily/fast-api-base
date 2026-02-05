import asyncio
from typing import AsyncGenerator, Generator

# from unittest.mock import Mock

import pytest
import pytest_asyncio

# from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import schemas
from app.api.deps import get_db
from app.core import celery_app
from app.core.security import JWTHandler
from app.crud import crud_user
from app.db import Base
from app.db import session as db_session
from app.db.init_db import init_db
from app.main import app, settings
from app.models.user import User
from app.utils import redis_client

ASYNC_SQLALCHEMY_DATABASE_URL = str(settings.POSTGRES_ASYNC_URI_TEST)

async_engine = create_async_engine(ASYNC_SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db() -> AsyncGenerator:
    async with async_session() as db:
        yield db
        await db.commit()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def patch_async_session_maker(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(db_session, "async_session", async_session)


# @pytest.fixture(scope="function", autouse=True)
# def celery_app_mock(monkeypatch: pytest.MonkeyPatch):
#     celery_app_mock = Mock()
#     monkeypatch.setattr(celery_app, "celery_app", celery_app_mock)
#     return celery_app_mock


@pytest.fixture(scope="session")
def event_loop(request) -> Generator:  # noqa: indirect usage
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        async with async_engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
        await init_db(db=session)
        yield session

    await async_engine.dispose()
    await redis_client.connection_pool.disconnect()


@pytest_asyncio.fixture(scope="module")
async def transport() -> ASGITransport:
    return ASGITransport(app=app)


@pytest_asyncio.fixture(scope="module")
async def client(transport: ASGITransport) -> AsyncClient:
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def super_user(db: AsyncSession) -> User:
    user = await crud_user.user.get_by_username(
        db=db, username=settings.FIRST_SUPERADMIN
    )
    assert user is not None
    return user


@pytest_asyncio.fixture(scope="function")
async def super_user_token(super_user: User) -> dict[str, str]:
    access_token = JWTHandler.encode(
        payload={"sub": "access", "id": str(super_user.id)}
    )
    return {"Authorization": f"Bearer {access_token}"}
