import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable

from fastapi import Request
from fastapi.applications import FastAPI
from fastapi.dependencies.utils import (
    get_body_field,
    get_dependant,
    get_parameterless_sub_dependant,
)
from fastapi.responses import PlainTextResponse
from fastapi.routing import APIRoute, request_response
from starlette.status import HTTP_504_GATEWAY_TIMEOUT
from starlette.types import ASGIApp, Receive, Scope, Send

from pccommon.tracing import trace_request

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: Exception) -> Any:
    logger.exception("Exception when handling request", exc_info=exc)
    raise


def with_timeout(
    timeout_seconds: float,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def with_timeout_(func: Callable[..., Any]) -> Callable[..., Any]:
        if asyncio.iscoroutinefunction(func):
            logger.debug("Adding timeout to function %s", func.__name__)

            @wraps(func)
            async def inner(*args: Any, **kwargs: Any) -> Any:
                start_time = time.monotonic()
                try:
                    return await asyncio.wait_for(
                        func(*args, **kwargs), timeout=timeout_seconds
                    )
                except asyncio.TimeoutError as e:
                    process_time = time.monotonic() - start_time
                    # don't have a request object here to get custom dimensions.
                    log_dimensions = {
                        "request_time": process_time,
                    }
                    logger.exception(
                        f"Request timeout {e}",
                        extra=log_dimensions,
                    )

                    ref_id = log_dimensions.get("ref_id")
                    debug_msg = (
                        f" Debug information for support: {ref_id}" if ref_id else ""
                    )

                    return PlainTextResponse(
                        f"The request exceeded the maximum allowed time, please"
                        " try again. If the issue persists, please contact "
                        "planetarycomputer@microsoft.com."
                        f"\n\n{debug_msg}",
                        status_code=HTTP_504_GATEWAY_TIMEOUT,
                    )

            return inner
        else:
            return func

    return with_timeout_


def add_timeout(app: FastAPI, timeout_seconds: float) -> None:
    for route in app.router.routes:
        if isinstance(route, APIRoute):
            new_endpoint = with_timeout(timeout_seconds)(route.endpoint)
            route.endpoint = new_endpoint
            route.dependant = get_dependant(path=route.path_format, call=route.endpoint)
            for depends in route.dependencies[::-1]:
                route.dependant.dependencies.insert(
                    0,
                    get_parameterless_sub_dependant(
                        depends=depends, path=route.path_format
                    ),
                )
            # TODO: `get_body_field` was updated after fastapi==0.112.4
            # https://github.com/fastapi/fastapi/blob/999eeb6c76ff37f94612dd140ce8091932f56c54/fastapi/dependencies/utils.py#L830-L832  # noqa: E501
            route.body_field = get_body_field(
                dependant=route.dependant, name=route.unique_id
            )
            route.app = request_response(route.get_route_handler())


class TraceMiddleware:
    def __init__(self, app: ASGIApp, service_name: str):
        self.app = app
        self.service_name = service_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            request: Request = Request(scope, receive)
            await trace_request(self.service_name, request)

        await self.app(scope, receive, send)
