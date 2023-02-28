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

from pccommon.constants import X_REQUEST_ENTITY
from pccommon.logging import ServiceName, init_logging
from pccommon.middleware import (
    RequestTracingMiddleware,
    handle_exceptions,
    timeout_middleware,
)
from pccommon.openapi import fixup_schema
from pctiler.config import get_settings
from pctiler.endpoints import health, item, legend, pg_mosaic, vector_tiles, zarr

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

app.state.service_name = ServiceName.TILER

# Note:
# With titiler.pgstac >3.0, items endpoint has changed and use path-parameter
# /collections/{collectionId}/items/{itemId} instead of query-parameter
# https://github.com/stac-utils/titiler-pgstac/blob/d16102bf331ba588f31e131e65b07637d649b4bd/titiler/pgstac/main.py#L87-L92
app.include_router(
    item.pc_tile_factory.router,
    prefix=settings.item_endpoint_prefix,
    tags=["Item tile endpoints"],
)

app.include_router(
    pg_mosaic.pgstac_mosaic_factory.router,
    prefix=settings.mosaic_endpoint_prefix,
    tags=["PgSTAC Mosaic endpoints"],
)

app.include_router(
    legend.legend_router,
    prefix=settings.legend_endpoint_prefix,
    tags=["Legend endpoints"],
)

app.include_router(
    vector_tiles.vector_tile_router,
    prefix=settings.vector_tile_endpoint_prefix,
    tags=["Collection vector tile endpoints"],
)

app.include_router(
    zarr.zarr_factory.router,
    prefix=settings.zarr_endpoint_prefix,
    tags=["Preview"],
)

app.include_router(health.health_router, tags=["Liveliness/Readiness"])

app.add_middleware(RequestTracingMiddleware, service_name=ServiceName.TILER)


@app.middleware("http")
async def _timeout_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Add a timeout to all requests."""
    return await timeout_middleware(request, call_next, timeout=settings.request_timout)


@app.middleware("http")
async def _handle_exceptions(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    return await handle_exceptions(request, call_next)


add_exception_handlers(app, DEFAULT_STATUS_CODES)
add_exception_handlers(app, MOSAIC_STATUS_CODES)

app.add_middleware(CacheControlMiddleware, cachecontrol="public, max-age=3600")
app.add_middleware(TotalTimeMiddleware)

if settings.debug:
    app.add_middleware(LoggerMiddleware)

# Note: If requests are being sent through an application gateway like
# nginx-ingress, you may need to configure CORS through that system.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=[X_REQUEST_ENTITY],
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
            version=settings.api_version,
            routes=app.routes,
        )
        app.openapi_schema = fixup_schema(app.root_path, schema)
    return app.openapi_schema  # type: ignore


app.openapi = custom_openapi  # type: ignore
