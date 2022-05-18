import logging
from typing import Awaitable, Callable

from fastapi import HTTPException, Request, Response
from fastapi.applications import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

from pccommon.logging import get_custom_dimensions
from pccommon.tracing import trace_request

logger = logging.getLogger(__name__)


async def handle_exceptions(
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
            extra=get_custom_dimensions({"stackTrace": f"{e}"}, request),
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
