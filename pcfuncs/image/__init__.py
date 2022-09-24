import json
import logging
from typing import Any

import azure.functions as func
from funclib.errors import BBoxTooLargeError, InvalidInputError
from funclib.raster import Bbox, ExportFormats
from funclib.stamps.branding import LogoStamp
from funclib.tiles import PILTileSet, TileSet
from pydantic import ValidationError

from .models import ImageRequest, ImageResponse
from .settings import ImageSettings
from .utils import get_min_zoom, register_search_and_get_tile_url, upload_image

logger = logging.getLogger(__name__)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        logger.info("Request:")
        logger.info(json.dumps(body, indent=2))
    except ValueError:
        return func.HttpResponse(
            status_code=400,
            mimetype="application/text",
            body="Error: Invalid JSON",
        )

    try:
        parsed_request = ImageRequest(**body)
    except ValidationError as e:
        logger.warning(e.json(indent=2))
        return func.HttpResponse(
            status_code=400,
            mimetype="application/json",
            body=e.json(),
        )

    try:
        response = await handle_request(parsed_request)

        return func.HttpResponse(
            status_code=200,
            mimetype="application/json",
            body=response.json(),
        )
    except (BBoxTooLargeError, InvalidInputError) as e:
        logger.exception(e)
        return func.HttpResponse(
            status_code=400,
            mimetype="application/json",
            body=json.dumps({"error": str(e)}),
        )
    except Exception as e:
        logger.exception(e)

        return func.HttpResponse(
            status_code=500,
            mimetype="application/json",
        )


async def handle_request(req: ImageRequest) -> ImageResponse:
    settings = ImageSettings.get()
    geom = req.get_geometry()
    bbox = Bbox.from_geom(geom)
    render_options = req.get_render_options()

    # Get the min zoom for this collection.
    min_zoom = await get_min_zoom(
        collection_id=render_options.collection, data_api_url_override=req.data_api_url
    )

    # Collection the tiles covering the requested geometry.
    # Use the min zoom of the collection as a starting point.
    covering_tiles = TileSet.get_covering_tiles(
        bbox, req.cols, req.rows, min_zoom=min_zoom
    )
    if not covering_tiles:
        raise InvalidInputError("No tiles found for given geometry")
    if len(covering_tiles) > settings.max_tile_count:
        print(f"Too many tiles: {len(covering_tiles)}")
        raise BBoxTooLargeError(
            "Export area is too large for the minimum zoom for "
            f"collection {render_options.collection}."
        )

    # Register the search and get the tile URL for the mosaic.
    tile_url = await register_search_and_get_tile_url(
        req.cql, render_options=render_options, data_api_url_override=req.data_api_url
    )

    # Get the TileSet
    tile_set: TileSet[Any]
    if req.format == ExportFormats.PNG:
        tile_set = PILTileSet(tile_url, render_options=render_options)
    else:
        raise NotImplementedError(f"Export format {req.format} not implemented")

    # Create the mosaic from the covering tiles, crop to the geometry bounds,
    # and resample to the requested image size.
    mosaic = await tile_set.get_mosaic(covering_tiles)
    result = mosaic.crop(bbox).resample(req.cols, req.rows)

    # Optionally mask the image (TODO: implement with rasterio)
    if req.mask:
        result = mosaic.mask(geom)

    if req.show_branding:
        LogoStamp().apply(result.image)

    # Upload the image to output storage.
    result_url = upload_image(result.to_bytes(), req.get_collection())

    return ImageResponse(url=result_url)
