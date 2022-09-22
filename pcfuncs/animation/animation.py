import asyncio
import io
import logging
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Type

import aiohttp
from dateutil.relativedelta import relativedelta
from funclib.errors import BBoxTooLargeError
from funclib.stamps.stamp import FrameStamp
from mercantile import Bbox, Tile, tiles
from PIL import Image
from PIL.Image import Image as PILImage

from .constants import MAX_TILE_COUNT
from .frame import AnimationFrame
from .settings import AnimationSettings


class PcMosaicAnimation:
    def __init__(
        self,
        bbox: List[float],
        zoom: int,
        cql: Dict[str, Any],
        render_params: str,
        stamps: List[Type[FrameStamp]],
        frame_duration: int = 250,
    ):
        self.bbox = bbox
        self.zoom = zoom
        self.cql = cql
        self.render_params = render_params
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

    async def _get_tilejson(self, the_date: str) -> str:
        non_temporal_args = [
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
        frame_cql["filter"]["args"] = non_temporal_args
        logging.info(f"Registering {the_date}")

        async with aiohttp.ClientSession() as session:
            # Register the search and get the tilejson_url back
            async with session.post(self.registerUrl, json=frame_cql) as resp:
                mosaic_info = await resp.json()
            tilejson_href = [
                link["href"]
                for link in mosaic_info["links"]
                if link["rel"] == "tilejson"
            ][0]
            tilejson_url = f"{tilejson_href}?{self.render_params}"

            # Get the full tile path template
            async with session.get(tilejson_url) as resp:
                tilejson = await resp.json()
            return tilejson["tiles"][0]

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
        tile_path = await self._get_tilejson(date.isoformat())

        tasks: List[asyncio.Future[io.BytesIO]] = []
        for tile in self.tiles:
            url = (
                tile_path.replace("{x}", str(tile.x))
                .replace("{y}", str(tile.y))
                .replace("{z}", str(tile.z))
            )
            tasks.append(asyncio.ensure_future(self._get_tile(url)))

        tile_images: List[io.BytesIO] = list(await asyncio.gather(*tasks))
        bbox = Bbox(
            left=self.bbox[0], bottom=self.bbox[1], right=self.bbox[2], top=self.bbox[3]
        )
        frame = AnimationFrame(
            tiles=self.tiles,
            tile_images=tile_images,
            bbox=bbox,
            tile_size=self.tile_size,
            frame_count=frame_count,
            frame_number=frame_number,
            stamps=self.stamps,
        )

        return frame.get_mosaic()
