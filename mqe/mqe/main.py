"""FastAPI application using PGStac."""
import logging
import os
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import ORJSONResponse
from stac_fastapi.extensions.core import FieldsExtension, QueryExtension, SortExtension
from stac_fastapi.pgstac.config import Settings
from stac_fastapi.pgstac.db import close_db_connection, connect_to_db
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

from mqe.api import PCStacApi
from mqe.client import MQEClient
from mqe.config import API_DESCRIPTION, API_TITLE, API_VERSION, get_settings
from mqe.middleware import count_collection_requests
from mqe.search import MQESearch
from pqecommon.logging import init_logging
from pqecommon.openapi import fixup_schema

DEBUG: bool = os.getenv("DEBUG") == "TRUE" or False

# Initialize logging
init_logging("mqe")
logger = logging.getLogger(__name__)

# Get the root path if set in the environment
APP_ROOT_PATH = os.environ.get("APP_ROOT_PATH", "")
logger.info(f"APP_ROOT_PATH: {APP_ROOT_PATH}")
INCLUDE_TRANSACTIONS = os.environ.get("INCLUDE_TRANSACTIONS", "") == "yes"
logger.info(f"INCLUDE_TRANSACTIONS: {INCLUDE_TRANSACTIONS}")

# Allow setting of SQLAlchemy connection pools
POOL_SIZE = int(os.environ.get("POOL_SIZE", "1"))
logger.info(f"POOL_SIZE: {POOL_SIZE}")

extensions = [QueryExtension(), SortExtension(), FieldsExtension()]

api = PCStacApi(
    title=API_TITLE,
    description=API_DESCRIPTION,
    api_version=API_VERSION,
    settings=Settings(debug=DEBUG),
    client=MQEClient.create(),
    extensions=extensions,
    app=FastAPI(root_path=APP_ROOT_PATH, default_response_class=ORJSONResponse),
    search_request_model=MQESearch,
)

app: FastAPI = api.app

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _count_collection_requests(request, call_next):
    return await count_collection_requests(request, call_next)


@app.on_event("startup")
async def startup_event():
    """Connect to database on startup."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection."""
    await close_db_connection(app)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
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

        print(json.dumps(app.openapi_schema["paths"], indent=2))
        return schema


# app.openapi = custom_openapi  # type: ignore
