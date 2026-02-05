import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app import crud


@pytest.mark.asyncio
class TestUtils:

    async def test_db_log(
        self, client: AsyncClient, db: AsyncSession, super_user_token: dict[str, str]
    ):
        tracker_id = "test_id"

        response = await client.post(
            f"{settings.API_V1_STR}/utils/test-db-log?tracker_id={tracker_id}",
            headers=super_user_token,
        )

        await asyncio.sleep(0.1)
        assert response.status_code == 200

        log_record = await crud.request_log.get_by_tracker_id(
            db=db, tracker_id=tracker_id
        )

        assert log_record is not None
        assert log_record.tracker_id == tracker_id
        assert log_record.processing_time is not None
