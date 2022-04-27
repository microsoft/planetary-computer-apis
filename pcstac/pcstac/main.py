"""FastAPI application using PGStac."""
import logging
import os
from typing import Any, Awaitable, Callable, Dict

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import ORJSONResponse
from stac_fastapi.api.errors import DEFAULT_STATUS_CODES
from stac_fastapi.api.models import create_get_request_model, create_post_request_model
from stac_fastapi.pgstac.config import Settings
from stac_fastapi.pgstac.db import close_db_connection, connect_to_db
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

from pccommon.logging import ServiceName, init_logging
from pccommon.middleware import RequestTracingMiddleware, handle_exceptions
from pccommon.openapi import fixup_schema
from pccommon.redis import connect_to_redis
from pcstac.api import PCStacApi
from pcstac.client import PCClient
from pcstac.config import (
    API_DESCRIPTION,
    API_TITLE,
    API_VERSION,
    EXTENSIONS,
    get_settings,
)
from pcstac.errors import PC_DEFAULT_STATUS_CODES
from pcstac.search import PCSearch, PCSearchContent, PCSearchGetRequest

DEBUG: bool = os.getenv("DEBUG") == "TRUE" or False

# Initialize logging
init_logging(ServiceName.STAC)
logger = logging.getLogger(__name__)

# Get the root path if set in the environment
APP_ROOT_PATH = os.environ.get("APP_ROOT_PATH", "")
logger.info(f"APP_ROOT_PATH: {APP_ROOT_PATH}")

app_settings = get_settings()

search_get_request_model = create_get_request_model(
    EXTENSIONS, base_model=PCSearchGetRequest
)
search_post_request_model = create_post_request_model(EXTENSIONS, base_model=PCSearch)

api = PCStacApi(
    title=API_TITLE,
    description=API_DESCRIPTION,
    api_version=API_VERSION,
    settings=Settings(
        db_max_conn_size=app_settings.db_max_conn_size,
        db_min_conn_size=app_settings.db_min_conn_size,
        search_content_class=PCSearchContent,
        debug=DEBUG,
    ),
    client=PCClient.create(post_request_model=search_post_request_model),
    extensions=EXTENSIONS,
    app=FastAPI(root_path=APP_ROOT_PATH, default_response_class=ORJSONResponse),
    search_get_request_model=search_get_request_model,
    search_post_request_model=search_post_request_model,
    response_class=ORJSONResponse,
    exceptions={**DEFAULT_STATUS_CODES, **PC_DEFAULT_STATUS_CODES},
)

app: FastAPI = api.app

app.state.service_name = ServiceName.STAC

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(RequestTracingMiddleware, service_name=ServiceName.STAC)


@app.middleware("http")
async def _handle_exceptions(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    return await handle_exceptions(request, call_next)


@app.on_event("startup")
async def startup_event() -> None:
    """Connect to database on startup."""
    await connect_to_db(app)
    await connect_to_redis(app)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close database connection."""
    await close_db_connection(app)


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> PlainTextResponse:
    return PlainTextResponse(
        str(exc.detail), status_code=exc.status_code, headers=exc.headers
    )


@app.exception_handler(StarletteHTTPException)
async def base_http_exception_handler(
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
            version=app_settings.api_version,
            routes=app.routes,
        )
        app.openapi_schema = fixup_schema(app.root_path, schema)
        return schema
