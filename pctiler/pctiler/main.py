#!/usr/bin/env python3
import logging
import os
from typing import Awaitable, Callable, Dict, List

from fastapi import FastAPI, Request, Response
from fastapi.openapi.utils import get_openapi
from morecantile.defaults import tms as defaultTileMatrices
from morecantile.models import TileMatrixSet
from starlette.middleware.cors import CORSMiddleware
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.middleware import (
    CacheControlMiddleware,
    LoggerMiddleware,
    TotalTimeMiddleware,
)
from titiler.mosaic.errors import MOSAIC_STATUS_CODES
from titiler.pgstac.db import close_db_connection, connect_to_db

from pccommon.logging import ServiceName, init_logging
from pccommon.middleware import RequestTracingMiddleware, handle_exceptions
from pccommon.openapi import fixup_schema
from pctiler.config import get_settings
from pctiler.endpoints import health, item, legend, pg_mosaic

# Initialize logging
init_logging(ServiceName.TILER)
logger = logging.getLogger(__name__)

# Get the root path if set in the environment
APP_ROOT_PATH = os.environ.get("APP_ROOT_PATH", "")

settings = get_settings()

app = FastAPI(
    title=settings.title,
    openapi_url=settings.openapi_url,
    root_path=APP_ROOT_PATH,
)

app.include_router(
    item.pc_tile_factory.router,
    prefix=get_settings().item_endpoint_prefix,
    tags=["Item tile endpoints"],
)

app.include_router(
    pg_mosaic.pgstac_mosaic_factory.router,
    prefix=get_settings().mosaic_endpoint_prefix,
    tags=["PgSTAC Mosaic endpoints"],
)

app.include_router(
    legend.legend_router,
    prefix=get_settings().legend_endpoint_prefix,
    tags=["Legend endpoints"],
)

app.include_router(health.health_router, tags=["Liveliness/Readiness"])

app.add_middleware(RequestTracingMiddleware, service_name=ServiceName.TILER)


@app.middleware("http")
async def _handle_exceptions(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    return await handle_exceptions(ServiceName.TILER, request, call_next)


add_exception_handlers(app, DEFAULT_STATUS_CODES)
add_exception_handlers(app, MOSAIC_STATUS_CODES)

app.add_middleware(CacheControlMiddleware, cachecontrol="public, max-age=3600")
app.add_middleware(TotalTimeMiddleware)

if get_settings().debug:
    app.add_middleware(LoggerMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    """Connect to database on startup."""
    await connect_to_db(app)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close database connection."""
    await close_db_connection(app)


@app.get("/")
async def read_root() -> Dict[str, str]:
    return {"Hello": "Planetary Developer!"}


@app.get("/tileMatrixSets")
async def matrix_list() -> List[str]:
    return defaultTileMatrices.list()


@app.get("/tileMatrixSets/{tileMatrixSetId}")
async def matrix_definition(tileMatrixSetId: str) -> TileMatrixSet:
    logger.info(
        "Matrix definition requested",
        extra={
            "custom_dimensions": {
                "tileMatrixSetId": tileMatrixSetId,
            }
        },
    )
    return defaultTileMatrices.get(tileMatrixSetId)


def custom_openapi() -> Dict:
    if not app.openapi_schema:
        schema = get_openapi(
            title="Preview of Tile Access Features",
            version=get_settings().api_version,
            routes=app.routes,
        )
        app.openapi_schema = fixup_schema(app.root_path, schema)
    return app.openapi_schema  # type: ignore


app.openapi = custom_openapi  # type: ignore
