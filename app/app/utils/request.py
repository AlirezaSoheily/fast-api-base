import asyncio
import enum
import logging
import time

import httpx

from app.exceptions import InternalErrorException
from app.log import log
from app.utils import MessageCodes

logger = logging.getLogger(__name__)


class ErrorType(str, enum.Enum):
    General = "General"
    Timeout = "Timeout"


async def make_request(
    method: str,
    url: str,
    timeout: int = 100,
    do_logging: bool = True,
    raise_error: bool = True,
    verify: bool = True,
    basic_auth: httpx.BasicAuth | None = None,
    **kwargs,
) -> httpx.Response | str:
    start_time = time.time()
    async with httpx.AsyncClient(
        timeout=timeout, verify=verify, auth=basic_auth
    ) as client:
        request = client.build_request(method, url, **kwargs)

        try:
            response = await client.send(request)
            return response

        except (
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.WriteError,
            httpx.WriteTimeout,
        ) as e:
            # there is no provider_answer
            error_msg = f"{type(e)}: {e}"
            error_message_code = MessageCodes.provider_default_error
            response = None

        except (httpx.ReadError, httpx.ReadTimeout) as e:
            # there is a chance that provider api worked
            error_msg = f"{type(e)}: {e}"
            response = None
            if not raise_error:
                return ErrorType.Timeout

            error_message_code = MessageCodes.provider_timeout_error

        except Exception as e:
            # there is a chance that provider api worked
            error_msg = f"{type(e)}: {e}"
            error_message_code = MessageCodes.provider_timeout_error
            response = None

        finally:
            if do_logging:
                processing_time = round(time.time() - start_time, 4)
                try:
                    asyncio.create_task(
                        log.save_request_log(
                            request=request,
                            response=error_msg if response is None else response,
                            start_processing_at=start_time,
                            processing_time=processing_time,
                        )
                    )
                except Exception as e:
                    logger.error(
                        f"Error Happened on saving ws request log:\ndetails: {e}, url: {url}"
                    )

    raise InternalErrorException(msg_code=error_message_code)
