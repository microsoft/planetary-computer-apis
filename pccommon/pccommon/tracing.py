import json
import logging
import re
from typing import List, Optional, Tuple, Union, cast

from fastapi import Request
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace import execution_context
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.span import SpanKind
from opencensus.trace.tracer import Tracer
from starlette.datastructures import QueryParams

from pccommon.config import get_apis_config
from pccommon.constants import (
    HTTP_METHOD,
    HTTP_PATH,
    HTTP_URL,
    X_AZURE_REF,
    X_REQUEST_ENTITY,
)
from pccommon.logging import request_to_path
from pccommon.utils import get_request_ip

_config = get_apis_config()
logger = logging.getLogger(__name__)


exporter = (
    AzureExporter(
        connection_string=(
            f"InstrumentationKey={_config.app_insights_instrumentation_key}"
        )
    )
    if _config.app_insights_instrumentation_key
    else None
)

is_trace_enabled = exporter is not None


async def trace_request(
    service_name: str,
    request: Request,
) -> None:
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

            # Add request dimensions to the trace prior to calling the next middleware
            tracer.add_attribute_to_current_span(
                attribute_key="ref_id",
                attribute_value=request.headers.get(X_AZURE_REF),
            )
            tracer.add_attribute_to_current_span(
                attribute_key="request_entity",
                attribute_value=request.headers.get(X_REQUEST_ENTITY),
            )
            tracer.add_attribute_to_current_span(
                attribute_key="request_ip",
                attribute_value=get_request_ip(request),
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
            collection_id = cast(
                Optional[str], collection_id_match.group("collection_id")
            )
            item_id = cast(Optional[str], collection_id_match.group("item_id"))
            return (collection_id, item_id)
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

    # Collection and ids are List[str] per the spec,
    # but the client may allow just a single item
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
    if cql is None:
        return None
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


def add_stac_attributes_from_search(search_json: str, request: Request) -> None:
    """
    Try to add the Collection ID and Item ID from a search to the current span.
    """
    collection_id, item_id = parse_collection_from_search(
        json.loads(search_json), request.method, request.query_params
    )
    parent_span = getattr(request.state, "parent_span", None)

    current_span = execution_context.get_current_span() or parent_span

    if current_span:
        if collection_id is not None:
            current_span.add_attribute("collection", collection_id)
            if item_id is not None:
                current_span.add_attribute("item", item_id)
    else:
        logger.warning("No active or parent span available for adding attributes.")


def parse_collection_from_search(
    body: dict,
    method: str,
    query_params: QueryParams,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse the collection id from a search request.

    The search endpoint is a bit of a special case. If it's a GET, the collection
    and item ids are in the querystring. If it's a POST, the collection and item may
    be in either a CQL-JSON or CQL2-JSON filter body, or a query/stac-ql body.
    """
    if method.lower() == "get":
        collection_id = query_params.get("collections")
        item_id = query_params.get("ids")
        return (collection_id, item_id)
    elif method.lower() == "post":
        try:
            if body.get("collections") is not None:
                return _parse_queryjson(body)
            elif "filter" in body:
                return _parse_cqljson(body["filter"])
        except json.JSONDecodeError as e:
            logger.warning(
                "Unable to parse search body as JSON. Ignoring collection"
                f"parameter. {e}"
            )
    return (None, None)
