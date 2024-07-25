import dataclasses
import logging
from typing import Annotated, Literal, Optional, List, Type
from urllib.parse import quote_plus, urljoin

import fastapi
from pydantic import conint
import pystac
from fastapi import Body, Depends, Path, Query, Request, Response
from fastapi.templating import Jinja2Templates
from geojson_pydantic.features import Feature
from html_sanitizer.sanitizer import Sanitizer
from starlette.responses import HTMLResponse
from titiler.core.dependencies import (
    CoordCRSParams,
    DstCRSParams,
    DefaultDependency,
)
from titiler.core.factory import MultiBaseTilerFactory, img_endpoint_params
from titiler.core.resources.enums import ImageType
from titiler.pgstac.dependencies import get_stac_item

from pccommon.config import get_render_config
from pctiler.colormaps import PCColorMapParams
from pctiler.config import get_settings
from pctiler.endpoints.dependencies import get_endpoint_function
from pctiler.reader import ItemSTACReader, ReaderParams

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class SubdatasetParams(DefaultDependency):
    """Assets, Expression and Asset's band Indexes parameters."""

    subdataset_name: Annotated[
        Optional[str],
        Query(
            title="Subdataset name",
            description="The name of a subdataset within the asset.",
        ),
    ] = None
    subdataset_bands: Annotated[
        Optional[List[int]],
        Query(
            title="Subdataset bands",
            description="The name of a subdataset within the asset.",
        ),
    ] = None


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


@dataclasses.dataclass
class MyMultiBaseTilerFactory(MultiBaseTilerFactory):
    subdataset_dependency: Type[DefaultDependency] = SubdatasetParams
    private_router: fastapi.APIRouter = dataclasses.field(
        default_factory=fastapi.APIRouter
    )

    def tile(self):  # noqa: C901
        """Register /tiles endpoint."""

        @self.router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params, deprecated=True)
        @self.router.get(
            r"/tiles/{z}/{x}/{y}.{format}", **img_endpoint_params, deprecated=True
        )
        @self.router.get(
            r"/tiles/{z}/{x}/{y}@{scale}x", **img_endpoint_params, deprecated=True
        )
        @self.router.get(
            r"/tiles/{z}/{x}/{y}@{scale}x.{format}",
            **img_endpoint_params,
            deprecated=True,
        )
        @self.router.get(r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **img_endpoint_params,
        )
        def tile(
            request: Request,
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
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                f"Identifier selecting one of the TileMatrixSetId supported (default: '{self.default_tms}')",
            ] = self.default_tms,
            scale: Annotated[
                conint(gt=0, le=4), "Tile size scale. 1=256x256, 2=512x512..."
            ] = 1,
            format: Annotated[
                ImageType,
                "Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",
            ] = None,
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            tile_params=Depends(self.tile_dependency),
            post_process=Depends(self.process_dependency),
            rescale=Depends(self.rescale_dependency),
            color_formula=Depends(self.color_formula_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            reader_params=Depends(self.reader_dependency),
            env=Depends(self.environment_dependency),
            subdataset_params=Depends(self.subdataset_dependency),
        ):
            endpoint = get_endpoint_function(
                self.private_router, path="/tiles/{z}/{x}/{y}", method=request.method
            )
            return endpoint(z, x, y, tileMatrixSetId, scale, format, src_path, layer_params, dataset_params, tile_params, post_process, rescale, color_formula, colormap, render_params, reader_params, env)
 


pc_tile_factory = MyMultiBaseTilerFactory(
    reader=ItemSTACReader,
    path_dependency=ItemPathParams,
    colormap_dependency=PCColorMapParams,
    reader_dependency=ReaderParams,
    router_prefix=get_settings().item_endpoint_prefix,
    # We remove the titiler default `/map` viewer
    add_viewer=False,
    private_router=MultiBaseTilerFactory(
        reader=ItemSTACReader,
        path_dependency=ItemPathParams,
        colormap_dependency=PCColorMapParams,
        reader_dependency=ReaderParams,
        router_prefix=get_settings().item_endpoint_prefix,
        # We remove the titiler default `/map` viewer
        add_viewer=False,
    ).router
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
