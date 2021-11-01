import logging
import re
from typing import Awaitable, Callable, Optional, Tuple

from fastapi import Request, Response
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.span import SpanKind
from opencensus.trace.tracer import Tracer

from pccommon.logging import log_collection_request, request_to_path
from pccommon.metrics import stats_recorder, view_manager
from pccommon.tracing import (
    HTTP_METHOD,
    HTTP_PATH,
    HTTP_STATUS_CODE,
    HTTP_URL,
    exporter,
)

logger = logging.getLogger(__name__)


browse_request_measure = measure_module.MeasureInt(
    "browse-request-count",
    "Browsing requests under a given collection",
    "browse-request",
)
browse_request_view = view_module.View(
    "Browse request view",
    browse_request_measure.description,
    ["collection", "item", "requestPath"],
    browse_request_measure,
    aggregation_module.CountAggregation(),
)

_log_metrics = view_manager and stats_recorder and exporter

if _log_metrics:
    view_manager.register_view(browse_request_view)
    mmap = stats_recorder.new_measurement_map()

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
    if _log_metrics:
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
                attribute_key=HTTP_PATH, attribute_value=request_to_path(request)
            )
            tracer.add_attribute_to_current_span(
                attribute_key=HTTP_METHOD, attribute_value=str(request.method)
            )
            tracer.add_attribute_to_current_span(
                attribute_key="service", attribute_value="stac"
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


async def count_collection_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    if _log_metrics:
        tmap = tag_map_module.TagMap()
        (collection_id, item_id) = _collection_item_from_request(request)
        if collection_id:
            tmap.insert("collection", collection_id)
            if item_id:
                tmap.insert("item", item_id)
            log_collection_request("stac", logger, collection_id, item_id, request)
        tmap.insert("requestPath", request_to_path(request))
        mmap.measure_int_put(browse_request_measure, 1)
        mmap.record(tmap)
    return await call_next(request)
