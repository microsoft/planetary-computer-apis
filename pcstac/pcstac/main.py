"""FastAPI application using PGStac."""
import logging
import os
from typing import Any, Awaitable, Callable, Dict, List

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import ORJSONResponse
from stac_fastapi.api.errors import DEFAULT_STATUS_CODES
from stac_fastapi.api.models import create_get_request_model, create_post_request_model
from stac_fastapi.extensions.core import (
    ContextExtension,
    FieldsExtension,
    FilterExtension,
    QueryExtension,
    SortExtension,
    TokenPaginationExtension,
)
from stac_fastapi.pgstac.config import Settings
from stac_fastapi.pgstac.db import close_db_connection, connect_to_db
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

from pccommon.logging import init_logging
from pccommon.middleware import handle_exceptions
from pccommon.openapi import fixup_schema
from pcstac.api import PCStacApi
from pcstac.client import PCClient
from pcstac.config import API_DESCRIPTION, API_TITLE, API_VERSION, get_settings
from pcstac.errors import PC_DEFAULT_STATUS_CODES
from pcstac.middleware import trace_request
from pcstac.search import PCSearch

DEBUG: bool = os.getenv("DEBUG") == "TRUE" or False

# Initialize logging
init_logging("stac")
logger = logging.getLogger(__name__)

# Get the root path if set in the environment
APP_ROOT_PATH = os.environ.get("APP_ROOT_PATH", "")
logger.info(f"APP_ROOT_PATH: {APP_ROOT_PATH}")
INCLUDE_TRANSACTIONS = os.environ.get("INCLUDE_TRANSACTIONS", "") == "yes"
logger.info(f"INCLUDE_TRANSACTIONS: {INCLUDE_TRANSACTIONS}")

# Allow setting of SQLAlchemy connection pools
POOL_SIZE = int(os.environ.get("POOL_SIZE", "1"))
logger.info(f"POOL_SIZE: {POOL_SIZE}")

extensions = [
    QueryExtension(),
    SortExtension(),
    FieldsExtension(),
    FilterExtension(),
    TokenPaginationExtension(),
    ContextExtension(),
]

# Planetary Computer conformance classes differ from the default
# stac-fastapi case so they are manually specified
cql_conformance_classes: List[str] = [
    "https://api.stacspec.org/v1.0.0-beta.3/item-search/#fields",
    "https://api.stacspec.org/v1.0.0-beta.3/item-search#filter",
    "https://api.stacspec.org/v1.0.0-beta.3/item-search#filter:cql-json",
    "https://api.stacspec.org/v1.0.0-beta.3/item-search#filter:filter",
    "https://api.stacspec.org/v1.0.0-beta.3/item-search#filter:item-search-filter",
    "https://api.stacspec.org/v1.0.0-beta.3/item-search#filter:basic-spatial-operators",
    (
        "https://api.stacspec.org/v1.0.0-beta.3/item-search"
        "#filter:basic-temporal-operators"
    ),
    "https://api.stacspec.org/v1.0.0-beta.3/item-search/#sort",
    "https://api.stacspec.org/v1.0.0-beta.3/item-search/#query",
]

collections_conformance_classes: List[str] = [
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
]

extra_conformance_classes = cql_conformance_classes + collections_conformance_classes

search_get_request_model = create_get_request_model(extensions)
search_post_request_model = create_post_request_model(extensions, base_model=PCSearch)

api = PCStacApi(
    title=API_TITLE,
    description=API_DESCRIPTION,
    api_version=API_VERSION,
    settings=Settings(debug=DEBUG),
    client=PCClient.create(
        post_request_model=search_post_request_model,
        extra_conformance_classes=extra_conformance_classes,
    ),
    extensions=extensions,
    app=FastAPI(root_path=APP_ROOT_PATH, default_response_class=ORJSONResponse),
    search_get_request_model=search_get_request_model,
    search_post_request_model=search_post_request_model,
    response_class=ORJSONResponse,
    exceptions={**DEFAULT_STATUS_CODES, **PC_DEFAULT_STATUS_CODES},
)

app: FastAPI = api.app

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _handle_exceptions(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    return await handle_exceptions(request, call_next)


@app.middleware("http")
async def _trace_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    return await trace_request(request, call_next)


@app.on_event("startup")
async def startup_event() -> None:
    """Connect to database on startup."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close database connection."""
    await close_db_connection(app)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> PlainTextResponse:
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> PlainTextResponse:
    return PlainTextResponse(str(exc), status_code=400)


def custom_openapi() -> Dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema
    else:
        schema = get_openapi(
            title="Planetary Computer STAC API",
            version=get_settings().api_version,
            routes=app.routes,
        )
        app.openapi_schema = fixup_schema(app.root_path, schema)
        import json

        print(json.dumps(app.openapi_schema["paths"], indent=2))  # type: ignore
        return schema
