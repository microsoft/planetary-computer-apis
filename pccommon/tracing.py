import json
import logging
import re
from typing import Awaitable, Callable, List, Optional, Tuple, Union

from fastapi import Request, Response
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.span import SpanKind
from opencensus.trace.tracer import Tracer

from pccommon.config import CommonConfig
from pccommon.logging import ServiceName, request_to_path

config = CommonConfig.from_environment()
logger = logging.getLogger(__name__)


HTTP_PATH = COMMON_ATTRIBUTES["HTTP_PATH"]
HTTP_URL = COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_STATUS_CODE = COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]
HTTP_METHOD = COMMON_ATTRIBUTES["HTTP_METHOD"]

# Headers containing information about the requester's
# IP address. Checked in the order listed here.
X_AZURE_CLIENTIP = "X-Azure-ClientIP"
X_ORIGINAL_FORWARDED_FOR = "X-Original-Forwarded-For"
X_FORWARDED_FOR = "X-Forwarded-For"

exporter = (
    AzureExporter(
        connection_string=(
            f"InstrumentationKey={config.app_insights_instrumentation_key}"
        )
    )
    if config.app_insights_instrumentation_key is not None
    else None
)

is_trace_enabled = exporter is not None


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
            (collection_id, item_id) = await _collection_item_from_request(
                service_name, request
            )
            span.span_kind = SpanKind.SERVER

            # Throwing the main span into request state lets us create child spans
            # in downstream request processing, if there are specific things that
            # are slow.
            request.state.parent_span = span

            response = await call_next(request)

            tracer.add_attribute_to_current_span(
                attribute_key="request_ip",
                attribute_value=get_request_ip(request),
            )
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


collection_id_re = re.compile(
    r".*/collections/?(?P<collection_id>[a-zA-Z0-9\-\%]+)?(/items/(?P<item_id>.*))?.*"  # noqa
)


async def _collection_item_from_request(
    service_name: str,
    request: Request,
) -> Tuple[Optional[str], Optional[str]]:
    """Attempt to get collection and item ids from the request path or querystring."""
    url = request.url

    try:
        collection_id_match = collection_id_re.match(f"{url}")
        if collection_id_match:
            collection_id = collection_id_match.group("collection_id")
            item_id = collection_id_match.group("item_id")
            return (collection_id, item_id)
        elif service_name == ServiceName.STAC and url.path.strip("/").endswith(
            "/search"
        ):
            return await _parse_collection_from_search(request)
        else:
            collection_id = request.query_params.get("collection")
            # Some endpoints, like preview/, take an `items` parameter, but
            # conventionally it is a single item id
            item_id = request.query_params.get("item") or request.query_params.get(
                "items"
            )
            return (collection_id, item_id)
    except Exception as e:
        logger.exception(e)
        return (None, None)


def _should_trace_request(request: Request) -> bool:
    """
    Determine if we should trace a request.
        - Not a HEAD request
        - Not a health check endpoint
    """
    return (
        is_trace_enabled
        and request.method.lower() != "head"
        and not request.url.path.strip("/").endswith("_mgmt/ping")
    )


async def _parse_collection_from_search(
    request: Request,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse the collection id from a search request.

    The search endpoint is a bit of a special case. If it's a GET, the collection
    and item ids are in the querystring. If it's a POST, the collection and item may
    be in either a CQL-JSON or CQL2-JSON filter body, or a query/stac-ql body.
    """

    if request.method.lower() == "get":
        collection_id = request.query_params.get("collections")
        item_id = request.query_params.get("ids")
        return (collection_id, item_id)
    elif request.method.lower() == "post":
        try:
            body = await request.json()
            if "collections" in body:
                return _parse_queryjson(body)
            elif "filter" in body:
                return _parse_cqljson(body["filter"])
        except json.JSONDecodeError:
            logger.warning(
                "Unable to parse search body as JSON. Ignoring collection parameter."
            )
    return (None, None)


def _parse_cqljson(cql: dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse the collection id from a CQL-JSON filter.

    The CQL-JSON filter is a bit of a special case. It's a JSON object in either
    CQL or CQL2 syntax. Parse the object and look for the collection and item
    ids. If multiple collections or items are found, format them to a CSV.
    """
    collections = _iter_cql(cql, property_name="collection")
    ids = _iter_cql(cql, property_name="id")

    if isinstance(collections, list):
        collections = ",".join(collections)
    if isinstance(ids, list):
        ids = ",".join(ids)

    return (collections, ids)


def _parse_queryjson(query: dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse the collection and item ids from a traditional STAC API Item Search body.

    The query is a JSON object with relevant keys, "collections" and "ids".
    """
    collection_ids = query.get("collections")
    item_ids = query.get("ids")

    # Collection and ids are List[str] per the spec, but the client may allow just a single item
    if isinstance(collection_ids, list):
        collection_ids = ",".join(collection_ids)
    if isinstance(item_ids, list):
        item_ids = ",".join(item_ids)

    return (collection_ids, item_ids)


def _iter_cql(cql: dict, property_name: str) -> Optional[Union[str, List[str]]]:
    """
    Recurse through a CQL or CQL2 filter body, returning the value of the
    provided property name, if found. Typical usage will be to provide
    `collection` and `id`.
    """
    for _, v in cql.items():
        if isinstance(v, dict):
            result = _iter_cql(v, property_name)
            if result is not None:
                return result
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    if "property" in item:
                        if item["property"] == property_name:
                            return v[1]
                    else:
                        result = _iter_cql(item, property_name)
                        if result is not None:
                            return result
    # No collection was found
    return None


def get_request_ip(request: Request) -> str:
    """Gets the IP address of the request."""

    ip_header = (
        config.dev_for_ip
        or request.headers.get(X_AZURE_CLIENTIP)  # set by Front Door
        or request.headers.get(X_ORIGINAL_FORWARDED_FOR)
        or request.headers.get(X_FORWARDED_FOR)
    )

    # If multiple IPs, take the first one
    return ip_header.split(",")[0]
