import logging
from typing import Any, Awaitable, Callable, Coroutine

from fastapi import HTTPException, Request, Response
from fastapi.applications import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

from pccommon.logging import request_to_path
from pccommon.tracing import HTTP_METHOD, HTTP_PATH, HTTP_URL, trace_request

logger = logging.getLogger(__name__)


async def handle_exceptions(
    service_name: str,
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
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
                    "service": service_name,
                }
            },
        )
        raise


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Custom middleware to use opencensus request traces

    Middleware implementations that access a Request object directly
    will cause subsequent middleware or route handlers to hang. See

    https://github.com/tiangolo/fastapi/issues/394

    for more details on this implementation.

    An alternative approach is to use dependencies on the APIRouter, but
    the stac-fast api implementation makes that difficult without having
    to override much of the app initialization.
    """

    def __init__(self, app: FastAPI, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def set_body(self, request: Request) -> None:
        receive_ = await request._receive()

        async def receive() -> Message:
            return receive_

        request._receive = receive

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        await self.set_body(request)
        response = await trace_request(self.service_name, request, call_next)
        return response
