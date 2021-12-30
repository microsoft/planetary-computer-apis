import logging
import re
from typing import Awaitable, Callable, Optional, Tuple

from fastapi import Request, Response
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.span import SpanKind
from opencensus.trace.tracer import Tracer

from pccommon.config import CommonConfig
from pccommon.logging import request_to_path

config = CommonConfig.from_environment()
logger = logging.getLogger(__name__)


HTTP_PATH = COMMON_ATTRIBUTES["HTTP_PATH"]
HTTP_URL = COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_STATUS_CODE = COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]
HTTP_METHOD = COMMON_ATTRIBUTES["HTTP_METHOD"]

exporter = (
    AzureExporter(
        connection_string=(
            f"InstrumentationKey={config.app_insights_instrumentation_key}"
        )
    )
    if config.app_insights_instrumentation_key is not None
    else None
)

isTraceEnabled = exporter is not None


collection_id_re = re.compile(
    r".*/collections/?(?P<collection_id>[a-zA-Z0-9\-\%]+)?(/items/(?P<item_id>.*))?.*"  # noqa
)


def _collection_item_from_request(
    request: Request,
) -> Tuple[Optional[str], Optional[str]]:
    """Attempt to get collection and item ids from the request path or querystring."""
    collection_id_match = collection_id_re.match(f"{request.url}")
    if collection_id_match:
        collection_id = collection_id_match.group("collection_id")
        item_id = collection_id_match.group("item_id")
        return (collection_id, item_id)
    else:
        collection_id = request.query_params.get("collection")
        # Some endpoints, like preview/, take an `items`` parameter, but
        # conventionally it is a single item id
        item_id = request.query_params.get("item") or request.query_params.get("items")
        return (collection_id, item_id)


def _should_trace_request(request: Request) -> bool:
    """
    Determine if we should trace a request.
        - Not a HEAD request
        - Not a health check endpoint
    """
    return (
        isTraceEnabled
        and request.method.lower() != "head"
        and not request.url.path.strip("/").endswith("_mgmt/ping")
    )


async def trace_request(
    service_name: str,
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Construct a request trace with custom dimensions"""
    request_path = request_to_path(request).strip("/")
    if _should_trace_request(request):
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
                attribute_key=HTTP_METHOD, attribute_value=str(request.method)
            )
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_URL, attribute_value=str(request.url)
            )
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_PATH, attribute_value=request_path
            )
            tracer.add_attribute_to_current_span(
                attribute_key="service", attribute_value=service_name
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
