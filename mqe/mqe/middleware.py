import logging
import re
from urllib.parse import urlparse

from fastapi import Request, Response
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.stats import view as view_module

from pqecommon.logging import log_collection_request
from pqecommon.metrics import stats_recorder, view_manager


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

_log_metrics = view_manager and stats_recorder

if _log_metrics:
    view_manager.register_view(browse_request_view)
    mmap = stats_recorder.new_measurement_map()

collection_id_re = re.compile(
    r".*/collections/?(?P<collection_id>[a-zA-Z0-9\-\%]+)?(/items/(?P<item_id>.*))?.*"  # noqa
)


async def count_collection_requests(request: Request, call_next) -> Response:
    if _log_metrics:
        collection_id_match = collection_id_re.match(f"{request.url}")
        tmap = tag_map_module.TagMap()
        if collection_id_match:
            collection_id = collection_id_match.group("collection_id")
            item_id = collection_id_match.group("item_id")
            if collection_id:
                tmap.insert("collection", collection_id)
            if item_id:
                tmap.insert("item", item_id)
            log_collection_request("mqe", logger, collection_id, item_id, request)
        parsed_url = urlparse(f"{request.url}")
        tmap.insert("requestPath", parsed_url.path)
        mmap.measure_int_put(browse_request_measure, 1)
        mmap.record(tmap)
    return await call_next(request)
