import json
import logging
import time
from datetime import datetime
from typing import Callable

import starlette
from fastapi import BackgroundTasks, Request
from fastapi.responses import Response
from fastapi.routing import APIRoute
from httpx import Request as HttpxRequest
from httpx import Response as HttpxResponse

from app import crud, exceptions, models, schemas
from app.db import session as db_session

logger = logging.getLogger(__name__)

_UNSECURE_KEYS = [
    "username",
    "password",
]


async def save_request_log(
    request: Request | HttpxRequest,
    response: Response | HttpxResponse | str = None,
    trace_back: str = "",
    tracker_id: str | int | None = None,
    processing_time: float | None = None,
    user_id: int | None = None,
    request_log_type: models.RequestLogType = models.RequestLogType.Outgoing,
    start_processing_at: float | None = None,
) -> None:
    try:
        client_host = request.client.host
    except:
        client_host = ""

    try:
        path_params = str(request.path_params)
    except:
        path_params = "{}"

    try:
        query_params = str(request.query_params)
    except:
        query_params = "{}"

    try:
        status_code = response.status_code
    except:
        status_code = None

    service_name = str(request.url)

    method = request.method
    request_data = {
        "body": {},
        "path_params": path_params,
        "query_params": query_params,
    }
    try:
        if type(request) == Request:
            request_data["body"] = await request.json()

        elif type(request) == HttpxRequest:
            if (
                hasattr(request, "headers")
                and hasattr(request.headers, "get")
                and "xml" in request.headers.get("content-type")
            ):
                request_data["body"] = {"xml_body": request.content.decode()}
            else:
                request_data["body"] = json.loads(request.content)
        else:
            logger.error(f"extract request, request type: {type(request)}")
    except RuntimeError:
        pass
    except starlette.requests.ClientDisconnect:
        pass
    except Exception as e:
        logger.error(f"extract request body error: {e} {type(e)}")

    for unsecure_key in _UNSECURE_KEYS:
        if request_data["body"].get(unsecure_key):
            request_data["body"][unsecure_key] = "*****"

    response_data = ""
    if response:
        if type(response) is str:
            response_data = json.dumps({"exception": response})  # handle exceptions
        elif (
            hasattr(response, "headers")
            and hasattr(response.headers, "get")
            and response.headers.get("Location")
        ):  # this line handle redirects
            response_data = json.dumps(
                {"redirect_location": response.headers.get("Location")}
            )
        elif (
            hasattr(response, "headers")
            and hasattr(response.headers, "get")
            and "xml" in response.headers.get("content-type", "")
        ):
            response_data = json.dumps({"xml_body": response.content.decode()})
        else:
            try:
                response_data = response.body.decode()
            except Exception as e:
                response_data = str(response.content.decode())

    request_log_data = {
        "service_name": service_name,
        "method": method,
        "ip": client_host,
        "request": json.dumps(request_data),
        "response": response_data,
        "trace": trace_back,
        "processing_time": str(processing_time),
        "tracker_id": str(tracker_id) if tracker_id != None else "",
        "user_id": user_id,
        "type": request_log_type,
        "status_code": status_code,
        "start_processing_at": (
            datetime.fromtimestamp(start_processing_at) if start_processing_at else None
        ),
    }

    # TODO: save with celery
    try:
        request_log_in = schemas.RequestLogCreate(**request_log_data)

        async with db_session.async_session() as db:
            await crud.request_log.create(db=db, obj_in=request_log_in)
            await db.commit()

    except Exception as e:
        logger.error(f"save request log err: {type(e)}, {e}")


class LogRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()
            try:
                response: Response = await original_route_handler(request)
            except Exception as e:
                response = await exceptions.handle_exception(request, e)

            processing_time = round(time.time() - start_time, 4)
            tracker_id = None
            try:
                tracker_id = request.state.tracker_id
            except:
                pass

            user_id = None
            try:
                user_id = request.state.user_id
            except:
                pass

            if not response.background:
                tasks = BackgroundTasks()
                tasks.add_task(
                    save_request_log,
                    request,
                    response,
                    "",
                    tracker_id,
                    processing_time,
                    user_id,
                    models.RequestLogType.Incoming,
                    start_time,
                )
                response.background = tasks
            else:
                response.background.add_task(
                    save_request_log,
                    request,
                    response,
                    "",
                    tracker_id,
                    processing_time,
                    user_id,
                    models.RequestLogType.Incoming,
                    start_time,
                )
            return response

        return custom_route_handler
