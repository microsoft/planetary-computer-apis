import re
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Type

from cogeo_mosaic.backends import BaseBackend
from fastapi import Depends, HTTPException, Query, Request, Response
from fastapi.templating import Jinja2Templates
from rio_tiler.io import BaseReader
from rio_tiler.io.cogeo import COGReader
from starlette.responses import HTMLResponse, JSONResponse
from titiler.mosaic.factory import MosaicTilerFactory

from dqe.colormaps import PCColorMapParams
from dqe.config import get_settings
from dqe.reader import PCSQLiteMosaicBackend
from dqe.settings import MosaicSettings
from pqecommon.render import COLLECTION_RENDER_CONFIG
from pqecommon.utils import get_param_str

mosaic_settings = MosaicSettings()


def CollectionMosaicPathParams(collection: str) -> str:
    render_config = COLLECTION_RENDER_CONFIG.get(collection)

    if render_config and render_config.has_mosaic:
        return f"sqlite:///{mosaic_settings.dir}/{collection}.db:mosaic"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"No tiles for collection {collection}",
        )


@dataclass
class MapParams:
    collection: str = Query(..., description="STAC Collection ID")


@dataclass
class MosaicParams:
    """Create mosaic path from args"""

    layer: str = Query(..., description="Mosaic Layer name ('{collection}')")

    def __post_init__(
        self,
    ) -> None:
        """Define mosaic URL."""
        pattern = r"^(?P<collection>[a-zA-Z0-9-_]{1,32})$"
        match = re.match(pattern, self.layer)
        if not match:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid layer name: `{self.layer}`",
            )

        meta = match.groupdict()
        self.collection = meta["collection"]

        self.url = f"sqlite:///{mosaic_settings.dir}/{self.collection}.db:mosaic"


@dataclass
class CollectionMosaicFactory(MosaicTilerFactory):
    """Collection Tiler

    Contains routes for rendering MosaicJSON for baked-in
    sqlite MosaicJSON files (TODO: something more robust)."""

    reader: Type[BaseBackend] = PCSQLiteMosaicBackend
    dataset_reader: Type[BaseReader] = COGReader
    path_dependency: Callable[..., str] = CollectionMosaicPathParams
    colormap_dependency: Callable[..., Optional[Dict]] = PCColorMapParams

    router_prefix: str = get_settings().collection_endpoint_prefix

    templates = Jinja2Templates(directory="/opt/src/templates")

    def register_routes(self) -> None:
        self.register_map_info()
        self.register_map()

        return super().register_routes()

    def register_map_info(self) -> None:
        ############################################################################
        # Preview mosaic tiles
        ############################################################################
        @self.router.get("/map/info", name="map/info", response_class=JSONResponse)
        def map_info(
            request: Request, params: MapParams = Depends(MapParams)
        ) -> Response:
            collection_id = params.collection
            render_config = COLLECTION_RENDER_CONFIG.get(collection_id)
            if render_config is None or (not render_config.has_mosaic):
                return Response(
                    status_code=404,
                    content=f"No map available for collection {collection_id}",
                )

            return JSONResponse(
                status_code=200,
                content={
                    "initialZoom": (render_config.mosaic_preview_zoom or 13),
                    "initialCoords": render_config.mosaic_preview_coords,
                },
            )

    def register_map(self) -> None:
        ############################################################################
        # Preview mosaic tiles
        ############################################################################
        @self.router.get("/map", response_class=HTMLResponse)
        def map(request: Request, params: MapParams = Depends(MapParams)) -> Response:
            collection_id = params.collection
            render_config = COLLECTION_RENDER_CONFIG.get(collection_id)
            if render_config is None or (not render_config.has_mosaic):
                return Response(
                    status_code=404,
                    content=f"No map available for collection {collection_id}",
                )

            tilejson_url = self.url_for(request, "tilejson")
            tilejson_url += f"?collection={collection_id}"
            tilejson_url += f"&{get_param_str(render_config.render_params)}"

            info_url = self.url_for(request, "map/info")
            info_url += f"?collection={collection_id}"

            return self.templates.TemplateResponse(
                "mosaic_preview.html",
                context={
                    "request": request,
                    "tileJson": tilejson_url,
                    "infoUrl": info_url,
                },
            )


collection_mosaic_factory = CollectionMosaicFactory()
