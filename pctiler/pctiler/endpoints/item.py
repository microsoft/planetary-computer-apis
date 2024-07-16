import logging
from typing import Annotated, Callable, Optional
from urllib.parse import quote_plus, urljoin

import fastapi
import pystac
import starlette
from fastapi import Body, Depends, HTTPException, Query, Request, Response
from fastapi.templating import Jinja2Templates
from geojson_pydantic.features import Feature
from html_sanitizer.sanitizer import Sanitizer
from starlette.responses import HTMLResponse
from titiler.core.dependencies import CoordCRSParams, DstCRSParams
from titiler.core.factory import MultiBaseTilerFactory, img_endpoint_params
from titiler.core.resources.enums import ImageType
from titiler.pgstac.dependencies import get_stac_item

from pccommon.config import get_render_config
from pctiler.colormaps import PCColorMapParams
from pctiler.config import get_settings
from pctiler.reader import ItemSTACReader, ReaderParams

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore

logger = logging.getLogger(__name__)


def ItemPathParams(
    request: Request,
    collection: str = Query(..., description="STAC Collection ID"),
    item: str = Query(..., description="STAC Item ID"),
) -> pystac.Item:
    """STAC Item dependency."""
    return get_stac_item(request.app.state.dbpool, collection, item)


# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(
    directory=str(resources_files(__package__) / "templates")  # type: ignore
)


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


@pc_tile_factory.router.post(
    r"/crop",
    **img_endpoint_params,
)
@pc_tile_factory.router.post(
    r"/crop.{format}",
    **img_endpoint_params,
)
@pc_tile_factory.router.post(
    r"/crop/{width}x{height}.{format}",
    **img_endpoint_params,
)
def geojson_crop(  # type: ignore
    request: fastapi.Request,
    geojson: Annotated[
        Feature, Body(description="GeoJSON Feature.")  # noqa: F722,E501
    ],
    format: Annotated[
        ImageType,
        "Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",  # noqa: E501,F722
    ] = None,  # type: ignore[assignment]
    src_path=Depends(pc_tile_factory.path_dependency),
    coord_crs=Depends(CoordCRSParams),
    dst_crs=Depends(DstCRSParams),
    layer_params=Depends(pc_tile_factory.layer_dependency),
    dataset_params=Depends(pc_tile_factory.dataset_dependency),
    image_params=Depends(pc_tile_factory.img_part_dependency),
    post_process=Depends(pc_tile_factory.process_dependency),
    rescale=Depends(pc_tile_factory.rescale_dependency),
    color_formula: Annotated[
        Optional[str],
        Query(
            title="Color Formula",  # noqa: F722
            description="rio-color formula (info: https://github.com/mapbox/rio-color)",  # noqa: E501,F722
        ),
    ] = None,
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
        rescale=rescale,
        color_formula=color_formula,
        colormap=colormap,
        render_params=render_params,
        reader_params=reader_params,
        env=env,
    )
    return result


def get_endpoint_function(
    router: fastapi.APIRouter, path: str, method: str
) -> Callable:
    for route in router.routes:
        match, _ = route.matches({"type": "http", "path": path, "method": method})
        if match == starlette.routing.Match.FULL:
            # The abstract BaseRoute doesn't have a `.endpoint` attribute,
            # but all of its subclasses do.
            return route.endpoint  # type: ignore [attr-defined]

    logger.warning(f"Could not find endpoint. method={method} path={path}")
    raise HTTPException(detail="Internal system error", status_code=500)
