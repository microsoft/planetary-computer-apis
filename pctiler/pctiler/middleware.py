import logging
from typing import Awaitable, Callable

from fastapi import HTTPException, Request, Response
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.span import SpanKind
from opencensus.trace.tracer import Tracer

from pccommon.logging import log_collection_request, request_to_path
from pccommon.tracing import (
    HTTP_METHOD,
    HTTP_PATH,
    HTTP_STATUS_CODE,
    HTTP_URL,
    LIVENESS_PATH,
    exporter,
)

logger = logging.getLogger(__name__)

_log_metrics = exporter is not None


async def trace_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    if (
        _log_metrics
        and request.method.lower() != "head"
        and request_to_path(request) != LIVENESS_PATH
    ):
        tracer = Tracer(
            exporter=exporter,
            sampler=ProbabilitySampler(1.0),
        )
        with tracer.span("main") as span:
            collection_id = request.query_params.get("collection")
            item_id = request.query_params.get("item")
            span.span_kind = SpanKind.SERVER

            # Throwing the main span into request state lets us create child spans
            # in downstream request processing, if there are specific things that
            # are slow.
            request.state.parent_span = span

            response = await call_next(request)

            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_PATH, attribute_value=request_to_path(request)
            )
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_STATUS_CODE, attribute_value=response.status_code
            )
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_URL, attribute_value=str(request.url)
            )
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_METHOD, attribute_value=str(request.method)
            )
            tracer.add_attribute_to_current_span(
                attribute_key="service", attribute_value="tiler"
            )
            tracer.add_attribute_to_current_span(
                attribute_key="in-server", attribute_value="true"
            )
            if collection_id is not None:
                tracer.add_attribute_to_current_span(
                    attribute_key="collection", attribute_value=collection_id
                )
                if item_id is not None:
                    tracer.add_attribute_to_current_span(
                        attribute_key="item", attribute_value=item_id
                    )

        return response
    else:
        return await call_next(request)


async def count_data_requests(request: Request, call_next):  # type: ignore
    if _log_metrics:
        log_collection_request(
            "tiler",
            logger,
            request.query_params.get("collection"),
            request.query_params.get("item"),
            request,
        )
    return await call_next(request)


async def handle_exceptions(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    try:
        return await call_next(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Exception when handling request", extra={
            "custom_dimensions": {
                "stackTrace": f"{e}",
                HTTP_URL: str(request.url),
                HTTP_METHOD: str(request.method),
                HTTP_PATH: request_to_path(request),
                "service": "tiler"
            }
        })
        raise
