import logging

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import Response
from starlette.requests import Request
from titiler.core.models.mapbox import TileJSON

from pccommon.config import get_render_config
from pccommon.config.collections import VectorTileset
from pctiler.config import get_settings
from pctiler.errors import VectorTileError, VectorTileNotFoundError
from pctiler.reader_vector_tile import VectorTileReader

logger = logging.getLogger(__name__)
settings = get_settings()

vector_tile_router = APIRouter()


@vector_tile_router.get(
    "/collections/{collection_id}/tilesets/{tileset_id}/tilejson.json",
    response_model=TileJSON,
    response_model_exclude_none=True,
)
async def get_tilejson(
    request: Request,
    collection_id: str = Path(description="STAC Collection ID"),
    tileset_id: str = Path(
        description="Registered tileset ID, see Collection metadata for valid values."
    ),
) -> TileJSON:
    """Get the tilejson for a given tileset."""

    tileset = _get_tileset_config(collection_id, tileset_id)

    tile_url = str(
        request.url_for(
            "get_tile",
            collection_id=collection_id,
            tileset_id=tileset_id,
            z="{z}",
            x="{x}",
            y="{y}",
        )
    )

    name = (
        tileset.name or f"Planetary Computer: {collection_id} {tileset_id} vector tiles"
    )

    tilejson = {
        "tiles": [tile_url],
        "name": name,
        "maxzoom": tileset.maxzoom,
        "minzoom": tileset.minzoom,
    }

    if tileset.bounds:
        tilejson["bounds"] = tileset.bounds
    if tileset.center:
        tilejson["center"] = tileset.center

    return TileJSON(**tilejson)


@vector_tile_router.get(
    "/collections/{collection_id}/tilesets/{tileset_id}/tiles/{z}/{x}/{y}",
    response_class=Response,
)
async def get_tile(
    request: Request,
    collection_id: str = Path(description="STAC Collection ID"),
    tileset_id: str = Path(
        description="Registered tileset ID, see Collection metadata for valid values."
    ),
    z: int = Path(description="Zoom"),
    x: int = Path(description="Tile column"),
    y: int = Path(description="Tile row"),
) -> Response:
    """Get a vector tile for a given tileset."""
    tileset = _get_tileset_config(collection_id, tileset_id)

    reader = VectorTileReader(collection_id, tileset, request)

    try:
        pbf = reader.get_tile(z, x, y)
    except Exception as e:
        logger.exception(e)
        raise VectorTileError(
            collection=collection_id,
            tileset_id=tileset_id,
            z=z,
            x=x,
            y=y,
        )

    if not pbf:
        raise VectorTileNotFoundError(
            collection=collection_id, tileset_id=tileset_id, z=z, x=x, y=y
        )

    return Response(
        content=pbf,
        media_type="application/x-protobuf",
        headers={"content-encoding": "gzip"},
    )


def _get_tileset_config(collection_id: str, tileset_id: str) -> VectorTileset:
    """Get the render configuration for a given collection."""
    config = get_render_config(collection_id)

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Collection {collection_id} has no registered tilesets",
        )

    tileset = config.get_vector_tileset(tileset_id)

    if not tileset:
        raise HTTPException(
            status_code=404,
            detail=f"Tileset {tileset_id} not found for collection {collection_id}",
        )

    return tileset
