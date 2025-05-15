import asyncio
import logging
from typing import Annotated, Optional
from urllib.parse import quote_plus, urljoin

import jinja2
import fastapi
import pystac
from pydantic import Field
from fastapi import Body, Depends, Query, Request, Response, Path
from fastapi.templating import Jinja2Templates
from geojson_pydantic.features import Feature
from html_sanitizer.sanitizer import Sanitizer
from starlette.responses import HTMLResponse
from titiler.core.dependencies import CoordCRSParams, DstCRSParams
from titiler.core.factory import MultiBaseTilerFactory, img_endpoint_params
from titiler.core.resources.enums import ImageType
from titiler.core.models.mapbox import TileJSON
from titiler.pgstac.dependencies import get_stac_item

from pccommon.config import get_render_config
from pccommon.redis import cached_result, stac_item_cache_key
from pctiler.colormaps import PCColorMapParams
from pctiler.config import get_settings
from pctiler.endpoints.dependencies import get_endpoint_function
from pctiler.reader import ItemSTACReader, ReaderParams

logger = logging.getLogger(__name__)


async def ItemPathParams(
    request: Request,
    collection: str = Query(..., description="STAC Collection ID"),
    item: str = Query(..., description="STAC Item ID"),
) -> pystac.Item:
    """
    STAC Item dependency.

    We attempt to read STAC item in from the redis cache to ameliorate high
    call volumes to the tiler, which can bottleneck on reading from pgstac.
    For example, say you have a few thousand calls/second to the tiler to get
    crops of STAC item assets. Presumably, someone will have run a STAC query to
    enumerage those items and fill the cache. Without the cache the bottleneck
    will become the large number of small, single-item queries to pgstac.
    Pretty soon, pgstac will be overwhelmed with queued queries and all the
    client requests will start to timeout.
    """

    # Async to sync nonsense
    def _get_stac_item_dict() -> dict:
        stac_item: pystac.Item = get_stac_item(
            request.app.state.dbpool, collection, item
        )
        return stac_item.to_dict()

    async def _fetch() -> dict:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _get_stac_item_dict)

    # It would have been great to reuse the cached value that the STAC service
    # fills, but there are two problems:
    # 1. titiler's get_stac_item() returns just the STAC item content from the database
    #    without injected links, and calling stac_fastapi here to reproduct
    #    the behavior of the STAC API feels wrong.
    # 2. We have no guarantee of temporal locality between the two services.
    #    In practice, say a client first enumerates many STAC items for analysis
    #    (cache filled). Then some time has passed, the cache expires, and the
    #    client starts issuing tiler calls to read asset data. Then, the cache,
    #    which was full, will be empty and we will have to call pgstac again.
    # It remains to be seen how we will handle this situation in general,
    # but for now we will make the STAC service and the tiler use different
    # keys in the cache, so they can individually fill their own caches.
    _item = await cached_result(
        _fetch, f"tiler:{stac_item_cache_key(collection, item)}", request
    )
    return pystac.Item.from_dict(_item)


jinja2_env = jinja2.Environment(
    loader=jinja2.ChoiceLoader([jinja2.PackageLoader(__package__, "templates")])
)
templates = Jinja2Templates(env=jinja2_env)

pc_tile_factory = MultiBaseTilerFactory(
    reader=ItemSTACReader,
    path_dependency=ItemPathParams,
    colormap_dependency=PCColorMapParams,
    reader_dependency=ReaderParams,
    router_prefix=get_settings().item_endpoint_prefix,
    # We remove the titiler default `/map` viewer
    add_viewer=False,
)


@pc_tile_factory.router.get("/map", response_class=HTMLResponse)
def map(
    request: Request,
    collection: str = Query(..., description="STAC Collection ID"),
    item: str = Query(..., description="STAC Item ID"),
) -> Response:
    render_config = get_render_config(collection)
    if render_config is None:
        return Response(
            status_code=404,
            content=f"No item map available for collection {collection}",
        )

    # Sanitize collection and item to avoid XSS when the values are templated
    # into the rendered html page
    sanitizer = Sanitizer()
    collection_sanitized = quote_plus(sanitizer.sanitize(collection))
    item_sanitized = quote_plus(sanitizer.sanitize(item))

    qs = render_config.get_full_render_qs(collection_sanitized, item_sanitized)
    tilejson_url = pc_tile_factory.url_for(request, "tilejson")
    tilejson_url += f"?{qs}"

    item_url = urljoin(
        get_settings().get_stac_api_href(request),
        f"collections/{collection_sanitized}/items/{item_sanitized}",
    )

    return templates.TemplateResponse(
        request,
        name="item_preview.html",
        context={
            "tileJson": tilejson_url,
            "collectionId": collection_sanitized,
            "itemId": item_sanitized,
            "itemUrl": item_url,
        },
    )

# crop/feature endpoint compat with titiler<0.15 (`/crop` was renamed `/feature`)
@pc_tile_factory.router.post(
    r"/crop",
    operation_id=f"{self.operation_prefix}postDataForGeoJSONCrop",
    **img_endpoint_params,
)
@pc_tile_factory.router.post(
    r"/crop.{format}",
            operation_id=f"{self.operation_prefix}postDataForGeoJSONWithFormatCrop",
    **img_endpoint_params,
)
@pc_tile_factory.router.post(
    r"/crop/{width}x{height}.{format}",
    operation_id=f"{self.operation_prefix}postDataForGeoJSONWithSizesAndFormatCrop",
    **img_endpoint_params,
)
def geojson_crop(  # type: ignore
    request: fastapi.Request,
    geojson: Annotated[
        Feature, Body(description="GeoJSON Feature.")  # noqa: F722,E501
    ],
    format: Annotated[
        ImageType,
        Field(
            description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg)."
        ),
    ] = None,  # type: ignore[assignment]
    src_path=Depends(pc_tile_factory.path_dependency),
    coord_crs=Depends(CoordCRSParams),
    dst_crs=Depends(DstCRSParams),
    layer_params=Depends(pc_tile_factory.layer_dependency),
    dataset_params=Depends(pc_tile_factory.dataset_dependency),
    image_params=Depends(pc_tile_factory.img_part_dependency),
    post_process=Depends(pc_tile_factory.process_dependency),
    colormap=Depends(pc_tile_factory.colormap_dependency),
    render_params=Depends(pc_tile_factory.render_dependency),
    reader_params=Depends(pc_tile_factory.reader_dependency),
    env=Depends(pc_tile_factory.environment_dependency),
) -> Response:
    """Create image from a geojson feature."""
    endpoint = get_endpoint_function(
        pc_tile_factory.router, path="/feature", method=request.method
    )
    result = endpoint(
        geojson=geojson,
        format=format,
        src_path=src_path,
        coord_crs=coord_crs,
        dst_crs=dst_crs,
        layer_params=layer_params,
        dataset_params=dataset_params,
        image_params=image_params,
        post_process=post_process,
        colormap=colormap,
        render_params=render_params,
        reader_params=reader_params,
        env=env,
    )
    return result


# /tiles endpoint compat with titiler<0.15, Optional `tileMatrixSetId`
@pc_tile_factory.router.get(
    "/tiles/{z}/{x}/{y}",
    operation_id=f"{pc_tile_factory.operation_prefix}getWebMercatorQuadTile",
    **img_endpoint_params,
)
@pc_tile_factory.router.get(
    "/tiles/{z}/{x}/{y}.{format}",
    operation_id=f"{pc_tile_factory.operation_prefix}getWebMercatorQuadTileWithFormat",
    **img_endpoint_params,
)
@pc_tile_factory.router.get(
    "/tiles/{z}/{x}/{y}@{scale}x",
    operation_id=f"{pc_tile_factory.operation_prefix}getWebMercatorQuadTileWithScale",
    **img_endpoint_params,
)
@pc_tile_factory.router.get(
    "/tiles/{z}/{x}/{y}@{scale}x.{format}",
    operation_id=f"{pc_tile_factory.operation_prefix}getWebMercatorQuadTileWithFormatAndScale",
    **img_endpoint_params,
)
def tile_compat(
    request: fastapi.Request,
    z: Annotated[
        int,
        Path(
            description="Identifier (Z) selecting one of the scales defined in the TileMatrixSet and representing the scaleDenominator the tile.",
        ),
    ],
    x: Annotated[
        int,
        Path(
            description="Column (X) index of the tile on the selected TileMatrix. It cannot exceed the MatrixHeight-1 for the selected TileMatrix.",
        ),
    ],
    y: Annotated[
        int,
        Path(
            description="Row (Y) index of the tile on the selected TileMatrix. It cannot exceed the MatrixWidth-1 for the selected TileMatrix.",
        ),
    ],
    scale: Annotated[
        int,
        Field(
            gt=0, le=4, description="Tile size scale. 1=256x256, 2=512x512..."
        ),
    ] = 1,
    format: Annotated[
        ImageType,
        Field(
            description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg)."
        ),
    ] = None,
    src_path=Depends(pc_tile_factory.path_dependency),
    reader_params=Depends(pc_tile_factory.reader_dependency),
    tile_params=Depends(pc_tile_factory.tile_dependency),
    layer_params=Depends(pc_tile_factory.layer_dependency),
    dataset_params=Depends(pc_tile_factory.dataset_dependency),
    post_process=Depends(pc_tile_factory.process_dependency),
    colormap=Depends(pc_tile_factory.colormap_dependency),
    render_params=Depends(pc_tile_factory.render_dependency),
    env=Depends(pc_tile_factory.environment_dependency),
) -> Response:
    """tiles endpoints compat."""
    endpoint = get_endpoint_function(
        pc_tile_factory.router, path="/tiles/{tileMatrixSetId}/{z}/{x}/{y}", method=request.method
    )
    result = endpoint(
        z=z,
        x=x,
        y=y,
        tileMatrixSetId="WebMercatorQuad",
        scale=scale,
        format=format,
        src_path=src_path,
        reader_params=reader_params,
        tile_params=tile_params,
        layer_params=layer_params,
        dataset_params=dataset_params,
        post_process=post_process,
        colormap=colormap,
        render_params=render_params,
        env=env,
    )
    return result


# /tilejson.json endpoint compat with titiler<0.15, Optional `tileMatrixSetId`
@pc_tile_factory.router.get(
    "/tilejson.json",
    response_model=TileJSON,
    responses={200: {"description": "Return a tilejson"}},
    response_model_exclude_none=True,
    operation_id=f"{pc_tile_factory.operation_prefix}getWebMercatorQuadTileJSON",
)
def tilejson_compat(
    request: fastapi.Request,
    tile_format: Annotated[
        Optional[ImageType],
        Query(
            description="Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
        ),
    ] = None,
    tile_scale: Annotated[
        int,
        Query(
            gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
        ),
    ] = 1,
    minzoom: Annotated[
        Optional[int],
        Query(description="Overwrite default minzoom."),
    ] = None,
    maxzoom: Annotated[
        Optional[int],
        Query(description="Overwrite default maxzoom."),
    ] = None,
    src_path=Depends(pc_tile_factory.path_dependency),
    reader_params=Depends(pc_tile_factory.reader_dependency),
    tile_params=Depends(pc_tile_factory.tile_dependency),
    layer_params=Depends(pc_tile_factory.layer_dependency),
    dataset_params=Depends(pc_tile_factory.dataset_dependency),
    post_process=Depends(pc_tile_factory.process_dependency),
    colormap=Depends(pc_tile_factory.colormap_dependency),
    render_params=Depends(pc_tile_factory.render_dependency),
    env=Depends(pc_tile_factory.environment_dependency),
) -> Response:
    """tilejson endpoint compat."""
    endpoint = get_endpoint_function(
        pc_tile_factory.router, path="/{tileMatrixSetId}/tilejson.json", method=request.method
    )
    result = endpoint(
        tileMatrixSetId="WebMercatorQuad",
        tile_format=tile_format,
        tile_scale=tile_scale,
        minzoom=minzoom,
        maxzoom=maxzoom,
        src_path=src_path,
        reader_params=reader_params,
        tile_params=tile_params,
        layer_params=layer_params,
        dataset_params=dataset_params,
        post_process=post_process,
        colormap=colormap,
        render_params=render_params,
        env=env,
    )
    return result
