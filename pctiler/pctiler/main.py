#!/usr/bin/env python3
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List, AsyncGenerator

from fastapi import FastAPI
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
from pccommon.middleware import TraceMiddleware, add_timeout, http_exception_handler
from pccommon.openapi import fixup_schema
from pctiler.config import get_settings
from pctiler.endpoints import (
    configuration,
    health,
    item,
    legend,
    pg_mosaic,
    vector_tiles,
)

# Initialize logging
init_logging(ServiceName.TILER)
logger = logging.getLogger(__name__)

# Get the root path if set in the environment
APP_ROOT_PATH = os.environ.get("APP_ROOT_PATH", "")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """FastAPI Lifespan."""
    await connect_to_db(app)
    yield
    await close_db_connection(app)


app = FastAPI(
    title=settings.title,
    openapi_url=settings.openapi_url,
    root_path=APP_ROOT_PATH,
    lifespan=lifespan,
)

app.state.service_name = ServiceName.TILER

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
pg_mosaic.add_collection_mosaic_info_route(
    app,
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
    configuration.configuration_router,
    prefix=settings.configuration_endpoint_prefix,
    tags=["Map configuration endpoints"],
)

app.include_router(health.health_router, tags=["Liveliness/Readiness"])

add_timeout(app, settings.request_timeout)
add_exception_handlers(app, DEFAULT_STATUS_CODES)
add_exception_handlers(app, MOSAIC_STATUS_CODES)


app.add_exception_handler(Exception, http_exception_handler)


app.add_middleware(TraceMiddleware, service_name=app.state.service_name)
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
