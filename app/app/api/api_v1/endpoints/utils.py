from typing import Any
import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas, crud
from app.api import deps
from app.core.celery_app import celery_app
from app.log import log
from app.api import deps
from app.models.user import GroupRoles, UserRoles
from app.utils.user_role import allowed_roles

router_with_log = APIRouter(route_class=log.LogRoute)
router = APIRouter()
logger = logging.getLogger(__name__)


@router_with_log.post("/test-db-log", response_model=schemas.Msg, status_code=200)
@allowed_roles(GroupRoles.__ADMINS__)
def test_db_log(
    request: Request,
    tracker_id: str,
    db=Depends(deps.get_db),
    current_user: models.User = Depends(deps.check_user_role),
) -> Any:
    """
    This is an example of using log route handler.
    """
    request.state.tracker_id = tracker_id

    return schemas.Msg(msg="your request logged in my db!")


@router.post("/test-celery/", response_model=schemas.Msg, status_code=201)
@allowed_roles(GroupRoles.__ADMINS__)
def test_celery(
    msg: schemas.Msg,
    current_user: models.User = Depends(deps.check_user_role),
) -> Any:
    """
    Test Celery worker.
    """
    task = celery_app.send_task("app.celery.worker.test_celery", args=[msg.msg])
    return {
        "msg": f"{msg.msg} - {task.id}",
    }


@router.post("/test-create_multi/", status_code=201)
@allowed_roles(GroupRoles.__ADMINS__)
async def test_create_multi(
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.check_user_role),
) -> Any:
    """
    Test CRUD create_multi
    """
    try:
        await crud.user.create_multi(
            db=db,
            objs_in=[
                schemas.UserCreate(username="test1", password="test1"),
                schemas.UserCreate(username="test2", password="test2"),
                schemas.UserCreate(username="test3", password="test3"),
            ],
        )
        return {"Done": True}
    except Exception as e:
        logger.error(e)
        return {"Done": False}


@router.post("/test-update_multi/", status_code=201)
@allowed_roles(GroupRoles.__ADMINS__)
async def test_update_multi(
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.check_user_role),
) -> Any:
    """
    Test CRUD update_multi
    """
    try:
        await crud.user.update_multi(
            db=db,
            db_objs=[
                await crud.user.get_by_username(db=db, username="test1"),
                await crud.user.get_by_username(db=db, username="test2"),
                await crud.user.get_by_username(db=db, username="test3"),
            ],
            objs_in=[
                schemas.UserUpdate(full_name="test_update1"),
                schemas.UserUpdate(full_name="test_update2"),
                schemas.UserUpdate(full_name="test_update3"),
            ],
            refresh=True,
        )
        return {"Done": True}
    except Exception as e:
        logger.error(e)
        return {"Done": False}
