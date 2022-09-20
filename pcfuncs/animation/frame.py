import io
from typing import Any, List

from mercantile import Bbox, Tile, xy_bounds
from PIL import Image
from PIL.Image import Image as PILImage

from .stamps.stamp import FrameStamp
from .utils import Point, geop_to_imgp, to_3857


class AnimationFrame:
    def __init__(
        self,
        tiles: List[Tile],
        tile_images: List[io.BytesIO],
        bbox: Bbox,
        tile_size: int,
        frame_number: int,
        frame_count: int,
        stamps: List[FrameStamp],
    ):
        self.tiles = tiles
        self.tile_images = tile_images
        self.tile_size = tile_size
        self.bbox = bbox
        self.num_cols = self._get_num_cols()
        self.num_rows = self._get_num_rows()
        self.px_width = self.num_cols * self.tile_size
        self.px_height = self.num_rows * self.tile_size
        self.frame_count = frame_count
        self.frame_number = frame_number
        self.stamps = stamps

    def _get_num_cols(self) -> int:
        return len(set([tile.x for tile in self.tiles]))

    def _get_num_rows(self) -> int:
        return int(len(self.tiles) / self.num_cols)

    def _crop(self, mosaic: PILImage) -> PILImage:
        # Web mercator min/max corners of full-tile bbox
        geo_ul = xy_bounds(self.tiles[0])
        geo_lr = xy_bounds(self.tiles[-1])
        tile_bounds = Bbox(geo_ul.left, geo_lr.bottom, geo_lr.right, geo_ul.top)

        # Web mercator of user bbox
        west, south, east, north = self.bbox
        webm_bbox = to_3857.transform_bounds(west, south, east, north)
        b_left, b_bottom, b_right, b_top = webm_bbox

        # Mosaic pixel-coordinates of min/max user bbox
        px_bbox_ul = geop_to_imgp(
            Point(x=b_left, y=b_top), tile_bounds, self.px_width, self.px_height
        )
        px_bbox_lr = geop_to_imgp(
            Point(x=b_right, y=b_bottom), tile_bounds, self.px_width, self.px_height
        )

        # Crop the mosaic to the pixel bounds of the user bbox
        box: Any = (px_bbox_ul.x, px_bbox_ul.y, px_bbox_lr.x, px_bbox_lr.y)
        return mosaic.crop(box)

    def get_mosaic(self) -> PILImage:

        mosaic = Image.new("RGBA", (self.px_width, self.px_height))

        x = 0
        y = 0
        for i, img in enumerate(self.tile_images):
            tile = Image.open(img)
            mosaic.paste(tile, (x * self.tile_size, y * self.tile_size))

            # Increment the row/col position for subsequent tiles
            if (i + 1) % self.num_rows == 0:
                y = 0
                x += 1
            else:
                y += 1

        cropped_frame = self._crop(mosaic)
        return self.stamp_frame(cropped_frame)

    def stamp_frame(self, mosaic: PILImage) -> PILImage:
        image = mosaic.copy()
        for Stamp in self.stamps:
            stamper = Stamp(self)
            image = stamper.apply(image)

        return image
