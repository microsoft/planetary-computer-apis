import logging
from urllib.parse import urlparse
from fastapi import Request
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.stats import view as view_module

from pqecommon.logging import log_collection_request
from pqecommon.metrics import stats_recorder, view_manager

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

_log_metrics = view_manager and stats_recorder

if _log_metrics:
    view_manager.register_view(data_request_count_view)
    mmap = stats_recorder.new_measurement_map()


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
            "dqe",
            logger,
            request.query_params.get("collection"),
            request.query_params.get("item"),
            request,
        )
    return await call_next(request)
