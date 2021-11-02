import logging
from typing import Awaitable, Callable
from urllib.parse import urlparse

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

# This list was extracted from every `get` query param in the
# OpenAPI specification at
# http https://planetarycomputer.microsoft.com/api/data/v1/openapi.json
# If a string doesn't appear in the list of attributes in a view, we can't
# send it as a tag to application insights.
# The Azure exporter for python opencensus doesn't seem to want to send more
# than 10 tags, so this list is a bespoke selection from the full list of
# query params, also with the requestPath.
all_query_params = [
    "assets",
    "collection",
    "colormap_name",
    "expression",
    "format",
    "height",
    "item",
    "items",
    "width",
    "requestPath",
]

data_request_count_measure = measure_module.MeasureInt(
    "data-request-count",
    "Requests for data (info, bounds, maps, etc.)",
    "data-request-count",
)
data_request_count_view = view_module.View(
    "Data request count view",
    data_request_count_measure.description,
    all_query_params,
    data_request_count_measure,
    aggregation_module.CountAggregation(),
)

_log_metrics = view_manager and stats_recorder and exporter

if _log_metrics:
    view_manager.register_view(data_request_count_view)
    mmap = stats_recorder.new_measurement_map()


async def trace_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    if _log_metrics:
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
        tmap = tag_map_module.TagMap()
        for k, v in request.query_params.items():
            tmap.insert(k, v)
        parsed_url = urlparse(f"{request.url}")
        tmap.insert("requestPath", parsed_url.path)
        mmap.measure_int_put(data_request_count_measure, 1)
        mmap.record(tmap)
        log_collection_request(
            "tiler",
            logger,
            request.query_params.get("collection"),
            request.query_params.get("item"),
            request,
        )
    return await call_next(request)
