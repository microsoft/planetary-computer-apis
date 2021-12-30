import logging
import re
from typing import Awaitable, Callable, Optional, Tuple

from fastapi import Request, Response
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.span import SpanKind
from opencensus.trace.tracer import Tracer

from pccommon.logging import ServiceName, request_to_path
from pccommon.tracing import (
    HTTP_METHOD,
    HTTP_PATH,
    HTTP_STATUS_CODE,
    HTTP_URL,
    exporter,
)

logger = logging.getLogger(__name__)

_log_metrics = exporter is not None

collection_id_re = re.compile(
    r".*/collections/?(?P<collection_id>[a-zA-Z0-9\-\%]+)?(/items/(?P<item_id>.*))?.*"  # noqa
)


def _collection_item_from_request(
    request: Request,
) -> Tuple[Optional[str], Optional[str]]:
    collection_id_match = collection_id_re.match(f"{request.url}")
    if collection_id_match:
        collection_id = collection_id_match.group("collection_id")
        item_id = collection_id_match.group("item_id")
        return (collection_id, item_id)
    else:
        return (None, None)


async def trace_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_path = request_to_path(request).strip("/")
    if _log_metrics and request.method.lower() != "head":
        tracer = Tracer(
            exporter=exporter,
            sampler=ProbabilitySampler(1.0),
        )
        with tracer.span("main") as span:
            (collection_id, item_id) = _collection_item_from_request(request)
            span.span_kind = SpanKind.SERVER

            # Throwing the main span into request state lets us create child spans
            # in downstream request processing, if there are specific things that
            # are slow.
            request.state.parent_span = span

            response = await call_next(request)

            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_STATUS_CODE, attribute_value=response.status_code
            )
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_URL, attribute_value=f"{request.url}"
            )
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_PATH, attribute_value=request_path
            )
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_METHOD, attribute_value=str(request.method)
            )
            tracer.add_attribute_to_current_span(
                attribute_key="service", attribute_value=ServiceName.STAC
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
