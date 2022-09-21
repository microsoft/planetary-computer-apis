import asyncio
import logging
import time
from typing import Awaitable, Callable

from fastapi import HTTPException, Request, Response
from fastapi.applications import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse
from starlette.status import HTTP_504_GATEWAY_TIMEOUT
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


async def timeout_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
    timeout: int,
) -> Response:
    try:
        start_time = time.time()
        return await asyncio.wait_for(call_next(request), timeout=timeout)

    except asyncio.TimeoutError:
        process_time = time.time() - start_time
        log_dimensions = get_custom_dimensions({"request_time": process_time}, request)

        logger.exception(
            "Request timeout",
            extra=log_dimensions,
        )

        ref_id = log_dimensions["custom_dimensions"].get("ref_id")
        debug_msg = f"Debug information for support: {ref_id}" if ref_id else ""

        return PlainTextResponse(
            f"The request exceeded the maximum allowed time, please try again."
            f"\n\n{debug_msg}",
            status_code=HTTP_504_GATEWAY_TIMEOUT,
        )
