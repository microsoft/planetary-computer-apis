import asyncio
import io
import logging
from copy import deepcopy
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import aiohttp
from dateutil.relativedelta import relativedelta
from funclib.errors import BBoxTooLargeError
from funclib.models import RenderOptions
from funclib.stamps.stamp import ImageStamp
from funclib.tiles import PILTileSet
from mercantile import Tile, tiles
from PIL import Image
from PIL.Image import Image as PILImage

from .constants import MAX_TILE_COUNT
from .settings import AnimationSettings


class PcMosaicAnimation:
    def __init__(
        self,
        bbox: List[float],
        zoom: int,
        cql: Dict[str, Any],
        render_options: RenderOptions,
        settings: AnimationSettings,
        stamps: List[Callable[[int, int], ImageStamp]],
        data_api_url_override: Optional[str] = None,
        frame_duration: int = 250,
    ):
        self.bbox = bbox
        self.zoom = zoom
        self.cql = cql
        self.render_options = render_options
        self.settings = settings
        self.data_api_url_override = data_api_url_override
        tiles_args: List[Any] = bbox + [zoom]
        self.tiles: List[Tile] = list(tiles(*tiles_args))
        self.frame_duration = frame_duration
        self.tile_size = 512

        settings = AnimationSettings.get()
        self.registerUrl = f"{settings.api_root_url}/mosaic/register/"
        self.async_limit = asyncio.Semaphore(settings.tile_request_concurrency)
        self.stamps = stamps

        if len(self.tiles) > MAX_TILE_COUNT:
            raise BBoxTooLargeError(
                f"Export area is too large, please draw a smaller area or zoom out."
                f" ({len(self.tiles)} of {MAX_TILE_COUNT} max tiles requested)"
            )

    def _get_frame_cql(self, the_date: str) -> Dict[str, Any]:
        new_args = [
            arg
            for arg in self.cql["filter"]["args"]
            if arg["args"][0]["property"] != "datetime"
        ] + [
            {
                "op": "<=",
                "args": [{"property": "datetime"}, {"timestamp": the_date}],
            }
        ]
        frame_cql = deepcopy(self.cql)
        frame_cql["filter"]["args"] = new_args
        return frame_cql

    async def _get_tile(self, url: str) -> io.BytesIO:
        async with aiohttp.ClientSession() as session:
            async with self.async_limit:
                # Download the image tile, block if exceeding concurrency limits
                async with await session.get(url) as resp:
                    if self.async_limit.locked():
                        logging.info("Concurrency limit reached, waiting...")
                        await asyncio.sleep(1)

                    if resp.status == 200:
                        return io.BytesIO(await resp.read())
                    else:
                        logging.warning(f"Tile request: {resp.status} {url}")
                        img_bytes = Image.new(
                            "RGB", (self.tile_size, self.tile_size), "gray"
                        )
                        empty = io.BytesIO()
                        img_bytes.save(empty, format="png")
                        return empty

    async def get(
        self, delta: relativedelta, start: datetime, frame_count: int
    ) -> io.BytesIO:
        frames: List[asyncio.Future[PILImage]] = []

        next_date = start
        for frame_number in range(frame_count):
            frames.append(
                asyncio.ensure_future(
                    self._get_frame(next_date, frame_count, frame_number)
                )
            )
            next_date += delta

        image_frames: List[PILImage] = list(await asyncio.gather(*frames))
        gif = image_frames[0]
        output = io.BytesIO()
        gif.save(
            output,
            format="GIF",
            append_images=image_frames[1:],
            optimize=True,
            save_all=True,
            duration=self.frame_duration,
            loop=0,
        )

        return output

    async def _get_frame(
        self, date: datetime, frame_count: int, frame_number: int
    ) -> PILImage:
        tile_set = await PILTileSet.create(
            self._get_frame_cql(date.isoformat()),
            self.render_options,
            self.settings,
            self.data_api_url_override,
        )

        raster = await tile_set.get_mosaic(self.tiles)
        image = raster.image
        for create_stamp in self.stamps:
            stamper = create_stamp(frame_count, frame_number)
            image = stamper.apply(image)

        return image
