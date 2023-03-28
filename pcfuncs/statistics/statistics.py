import asyncio
from typing import Any, Dict, List, Optional

from funclib.errors import BBoxTooLargeError
from funclib.models import RenderOptions
from funclib.raster import Bbox
from funclib.tiles import GDALTileSet
from mercantile import Tile, tiles
from pyproj import CRS
from rio_tiler.models import ImageData

from .constants import MAX_TILE_COUNT
from .settings import StatisticsSettings


class PcMosaicImage:
    def __init__(
        self,
        bbox: List[float],
        zoom: int,
        cql: Dict[str, Any],
        render_options: RenderOptions,
        settings: StatisticsSettings,
        data_api_url_override: Optional[str] = None,
    ):
        self.bbox = Bbox(bbox[0], bbox[1], bbox[2], bbox[3], crs=CRS.from_epsg(4326))
        self.zoom = zoom
        self.cql = cql
        self.render_options = render_options
        self.settings = settings
        self.data_api_url_override = data_api_url_override

        tiles_args: List[Any] = bbox + [zoom]
        self.tiles: List[Tile] = list(tiles(*tiles_args))
        self.tile_size = 512

        settings = StatisticsSettings.get()
        self.registerUrl = f"{settings.api_root_url}/mosaic/register/"
        self.async_limit = asyncio.Semaphore(settings.tile_request_concurrency)

        if len(self.tiles) > MAX_TILE_COUNT:
            raise BBoxTooLargeError(
                f"Export area is too large, please draw a smaller area or zoom out."
                f" ({len(self.tiles)} of {MAX_TILE_COUNT} max tiles requested)"
            )

    async def get(self) -> ImageData:
        tile_set = await GDALTileSet.create(
            self.cql["filter"],
            self.render_options,
            self.settings,
            self.data_api_url_override,
        )

        raster = await tile_set.get_mosaic(self.tiles)
        image = raster.crop(self.bbox).image
        return image
