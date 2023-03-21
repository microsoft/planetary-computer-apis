import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from functools import reduce
from typing import Any, Dict, List, Optional, Tuple, TypeVar

import mercantile
from PIL.Image import Image as PILImage
from pyproj import CRS, Transformer
from rio_tiler.models import ImageData

T = TypeVar("T", bound="Raster")


@dataclass
class Bbox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    crs: Optional[CRS] = None

    @property
    def width(self) -> float:
        return self.xmax - self.xmin

    @property
    def height(self) -> float:
        return self.ymax - self.ymin

    def to_list(self) -> List[float]:
        return [self.xmin, self.ymin, self.xmax, self.ymax]

    def reproject(self, crs: CRS) -> "Bbox":
        if self.crs is None:
            raise ValueError("Cannot reproject a Bbox without a CRS")
        if self.crs == crs:
            return self
        res = Transformer.from_crs(self.crs, crs, always_xy=True).transform_bounds(
            self.xmin, self.ymin, self.xmax, self.ymax
        )
        return Bbox(xmin=res[0], ymin=res[1], xmax=res[2], ymax=res[3], crs=crs)

    @classmethod
    def from_geom(cls, geom: Dict[str, Any]) -> "Bbox":
        bbox: mercantile.LngLatBbox = mercantile.geojson_bounds(geom)
        return cls(
            xmin=bbox.west,
            ymin=bbox.south,
            xmax=bbox.east,
            ymax=bbox.north,
            crs=CRS.from_epsg(4326),
        )

    @classmethod
    def from_tiles(cls, tiles: List[mercantile.Tile]) -> "Bbox":
        if len(tiles) == 0:
            raise ValueError("Cannot create a Bbox from an empty list of tiles")

        def reducer(
            acc: Tuple[float, float, float, float], tile: mercantile.Tile
        ) -> Tuple[float, float, float, float]:
            tile_bounds = mercantile.bounds(tile)
            return (
                min(acc[0], tile_bounds.west),
                min(acc[1], tile_bounds.south),
                max(acc[2], tile_bounds.east),
                max(acc[3], tile_bounds.north),
            )

        xmin, ymin, xmax, ymax = reduce(
            reducer, tiles, (float("inf"), float("inf"), float("-inf"), float("-inf"))
        )
        return cls(xmin, ymin, xmax, ymax, CRS.from_epsg(4326))


@dataclass
class RasterExtent:
    bbox: Bbox
    cols: int
    rows: int

    @property
    def cellwidth(self) -> float:
        return (self.bbox.xmax - self.bbox.xmin) / self.cols

    @property
    def cellheight(self) -> float:
        return (self.bbox.ymax - self.bbox.ymin) / self.rows

    def map_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        x_px = (x - self.bbox.xmin) / self.cellwidth
        y_px = (self.bbox.ymax - y) / self.cellheight
        return int(x_px), int(y_px)


class ExportFormats(str, Enum):
    def __str__(self) -> str:
        return self.value

    PNG = "png"
    COG = "cog"


class Raster(ABC):
    def __init__(self, extent: RasterExtent) -> None:
        self.extent = extent

    @abstractmethod
    def to_bytes(self, format: str = ExportFormats.PNG) -> io.BytesIO:
        ...

    @abstractmethod
    def crop(self: T, bbox: Bbox) -> T:
        ...

    @abstractmethod
    def resample(self: T, cols: int, rows: int) -> T:
        ...

    @abstractmethod
    def mask(self: T, geom: Dict[str, Any]) -> T:
        ...


class PILRaster(Raster):
    def __init__(self, extent: RasterExtent, image: PILImage) -> None:
        self.image = image
        super().__init__(extent)

    def to_bytes(self, format: str = ExportFormats.PNG) -> io.BytesIO:
        if format not in [ExportFormats.PNG]:
            raise ValueError(f"Unsupported format: {format}")
        img_bytes = io.BytesIO()
        self.image.save(img_bytes, format=format)
        img_bytes.seek(0)
        return img_bytes

    def crop(self, bbox: Bbox) -> "PILRaster":
        # Web mercator of user bbox
        if (
            not bbox.crs == self.extent.bbox.crs
            and bbox.crs is not None
            and self.extent.bbox.crs is not None
        ):
            bbox = bbox.reproject(self.extent.bbox.crs)

        col_min, row_min = self.extent.map_to_grid(bbox.xmin, bbox.ymax)
        col_max, row_max = self.extent.map_to_grid(bbox.xmax, bbox.ymin)

        box: Any = (col_min, row_min, col_max, row_max)
        cropped = self.image.crop(box)
        return PILRaster(
            extent=RasterExtent(
                bbox,
                cols=col_max - col_min,
                rows=row_max - row_min,
            ),
            image=cropped,
        )

    def resample(self, cols: int, rows: int) -> "PILRaster":
        return PILRaster(
            extent=RasterExtent(bbox=self.extent.bbox, cols=cols, rows=rows),
            image=self.image.resize((cols, rows)),
        )

    def mask(self, geom: Dict[str, Any]) -> "PILRaster":
        raise NotImplementedError("PILRaster does not support masking")


class GDALRaster(Raster):
    def __init__(self, extent: RasterExtent, image: ImageData) -> None:
        self.image = image
        super().__init__(extent)

    def to_bytes(self, format: str = ExportFormats.PNG) -> io.BytesIO:
        img_bytes = self.image.render(
            add_mask=True,
            img_format=format.upper(),
        )
        return io.BytesIO(img_bytes)

    def crop(self, bbox: Bbox) -> "GDALRaster":
        # Web mercator of user bbox
        if (
            not bbox.crs == self.extent.bbox.crs
            and bbox.crs is not None
            and self.extent.bbox.crs is not None
        ):
            bbox = bbox.reproject(self.extent.bbox.crs)

        col_min, row_min = self.extent.map_to_grid(bbox.xmin, bbox.ymax)
        col_max, row_max = self.extent.map_to_grid(bbox.xmax, bbox.ymin)

        data = self.image.data[:, row_min:row_max, col_min:col_max]
        mask = self.image.mask[row_min:row_max, col_min:col_max]
        cropped = ImageData(
            data,
            mask,
            assets=self.image.assets,
            crs=self.image.crs,
            bounds=bbox,
            band_names=self.image.band_names,
            metadata=self.image.metadata,
            dataset_statistics=self.image.dataset_statistics,
        )

        return GDALRaster(
            extent=RasterExtent(
                bbox,
                cols=col_max - col_min,
                rows=row_max - row_min,
            ),
            image=cropped,
        )

    def resample(self, cols: int, rows: int) -> "GDALRaster":
        return GDALRaster(
            extent=RasterExtent(bbox=self.extent.bbox, cols=cols, rows=rows),
            image=self.image.resize(rows, cols),  # type: ignore
        )

    def mask(self, geom: Dict[str, Any]) -> "GDALRaster":
        raise NotImplementedError("GDALRaster does not support masking")
