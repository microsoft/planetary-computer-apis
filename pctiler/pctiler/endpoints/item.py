import os
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Type
from urllib.parse import urljoin

import rasterio
from fastapi import Body, Depends, Query, Request, Response
from fastapi.templating import Jinja2Templates
from geojson_pydantic.features import Feature
from rio_tiler.io import MultiBaseReader
from starlette.responses import HTMLResponse
from titiler.core.dependencies import (
    AssetsBidxParams,
    DatasetParams,
    DatasetPathParams,
    ImageParams,
    RenderParams,
)
from titiler.core.factory import MultiBaseTilerFactory, img_endpoint_params
from titiler.core.resources.enums import ImageType
from titiler.core.utils import Timer

from pccommon.render import COLLECTION_RENDER_CONFIG
from pccommon.utils import get_param_str
from pctiler.colormaps import PCColorMapParams
from pctiler.config import get_settings
from pctiler.reader import ItemSTACReader
from pctiler.util import item_path_template


def ItemPathParams(collection: str, items: str) -> str:
    return os.path.join(
        get_settings().stac_api_url, f"collections/{collection}/items/{items}"
    )


@dataclass
class MapParams:
    collection: str = Query(..., description="STAC Collection ID")
    item: str = Query(..., description="STAC Item ID")


@dataclass
class ItemTileFactory(MultiBaseTilerFactory):
    """Item tiler

    Contains titiler routes for STAC Items, along with some
    custom routes.
    """

    reader: Type[MultiBaseReader] = ItemSTACReader

    colormap_dependency: Callable[..., Optional[Dict]] = PCColorMapParams

    path_dependency: Callable[..., str] = ItemPathParams

    router_prefix: str = get_settings().item_endpoint_prefix

    templates = Jinja2Templates(directory="/opt/src/templates")

    def register_routes(self) -> None:
        self.register_map()

        super().register_routes()

        self.register_poly_crop()

    def register_map(self) -> None:
        """Register /map endpoint"""

        ############################################################################
        # Map: Rendered map of Item
        ############################################################################

        @self.router.get("/map", response_class=HTMLResponse)
        def map(
            request: Request, map_params: MapParams = Depends(MapParams)
        ) -> Response:

            collection_id, item_id = (map_params.collection, map_params.item)

            render_config = COLLECTION_RENDER_CONFIG.get(collection_id)
            if render_config is None:
                return Response(
                    status_code=404,
                    content=f"No item map available for collection {collection_id}",
                )

            tilejson_params = get_param_str(
                {
                    "collection": collection_id,
                    "items": item_id,
                    "assets": ",".join(render_config.assets),
                }
            )

            tilejson_url = self.url_for(request, "tilejson")
            tilejson_url += f"?{tilejson_params}"

            item_url = urljoin(
                get_settings().stac_api_href,
                f"collections/{collection_id}/items/{item_id}",
            )

            return self.templates.TemplateResponse(
                "item_preview.html",
                context={
                    "request": request,
                    "tileJson": tilejson_url,
                    "collectionId": collection_id,
                    "itemId": item_id,
                    "itemUrl": item_url,
                    "renderParams": get_param_str(render_config.render_params),
                },
            )

    def register_poly_crop(self) -> None:
        @self.router.post(
            "/crop.{format}",
            **img_endpoint_params,
        )
        @self.router.post(
            "/crop/{width}x{height}.{format}",
            **img_endpoint_params,
        )
        def crop_by_geojson(
            collection_id: str = Query(..., description="ID of STAC collection"),
            item: str = Query(..., description="ID of STAC item"),
            format: ImageType = Query(..., description="Output image type."),
            asset_params: AssetsBidxParams = Depends(AssetsBidxParams),
            image_params: ImageParams = Depends(ImageParams),
            dataset_params: DatasetParams = Depends(DatasetParams),
            render_params: RenderParams = Depends(RenderParams),
            colormap: Callable[..., str] = Depends(PCColorMapParams),
            kwargs: Dict = Depends(self.additional_dependency),
            feature: Feature = Body(...),
        ) -> Response:
            """Create image from part of a dataset, masking with a polygon"""
            timings = []
            headers: Dict[str, str] = {}

            path_url = item_path_template.format(
                collection_id=collection_id, item_id=item
            )
            src_path = DatasetPathParams(url=path_url)

            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                        src_path, **self.reader_options
                    ) as src_dst:  # type:ignore
                        geojson_dict = feature.dict()
                        # The `bbox` property leads to issues if it is `None`
                        if geojson_dict["bbox"] is None:
                            del geojson_dict["bbox"]
                        data = src_dst.feature(
                            feature.dict(),
                            **asset_params.kwargs,
                            **image_params.kwargs,
                            **dataset_params.kwargs,
                            **kwargs,
                        )
                        dst_colormap = getattr(src_dst, "colormap", None)
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                image = data.post_process(
                    in_range=render_params.rescale_range,
                    color_formula=render_params.color_formula,
                )
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                content = image.render(
                    add_mask=render_params.return_mask,
                    img_format=format.driver,
                    colormap=colormap or dst_colormap,
                    **format.profile,
                    **render_params.kwargs,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            headers["Server-Timing"] = ", ".join(
                [f"{name};dur={time}" for (name, time) in timings]
            )

            return Response(content, media_type=format.mediatype, headers=headers)


pc_tile_factory = ItemTileFactory()
