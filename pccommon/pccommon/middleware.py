import logging
from typing import Awaitable, Callable

from fastapi import HTTPException, Request, Response

from pccommon.logging import request_to_path
from pccommon.tracing import HTTP_METHOD, HTTP_PATH, HTTP_URL

logger = logging.getLogger(__name__)


async def handle_exceptions(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    try:
        return await call_next(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Exception when handling request",
            extra={
                "custom_dimensions": {
                    "stackTrace": f"{e}",
                    HTTP_URL: str(request.url),
                    HTTP_METHOD: str(request.method),
                    HTTP_PATH: request_to_path(request),
                    "service": "tiler",
                }
            },
        )
        raise
