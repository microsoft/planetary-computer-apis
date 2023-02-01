from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import quote

import attr
import numpy
from pydantic import BaseModel
from rasterio.coords import BoundingBox
from rasterio.enums import ColorInterp, Resampling
from rasterio.io import DatasetReader, DatasetWriter, MemoryFile
from rio_tiler.models import ImageData
from rio_tiler.utils import get_array_statistics, non_alpha_indexes, resize_array


class RenderOptions(BaseModel):
    """Titiler render options.

    See the "Query Parameters" section of
    https://developmentseed.org/titiler/endpoints/stac/
    """

    collection: str

    pixel_selection: Optional[str] = None
    """Pixel selection method.

    One of: first, highest, lowest, mean, median, stdev
    """

    assets: Optional[Union[str, List[str]]] = None
    """Assets to render."""

    asset_bidx: Optional[Union[str, List[str]]] = None
    """Per asset band indexes (e.g. data|1,2,3, cog|1)"""

    expression: Optional[str] = None
    """Band math expression between assets (e.g. asset1 + asset2 / asset3)"""

    asset_expression: Optional[Union[str, List[str]]] = None
    """Per asset band expression (e.g. data|b1*b2+b3, cog|b1+b3)"""

    nodata: Optional[str] = None
    """Overwrite internal Nodata value"""

    unscale: Optional[bool] = None
    """Apply dataset internal Scale/Offset"""

    resampling: Optional[str] = None
    """rasterio resampling method. Default is nearest"""

    rescale: Optional[Union[str, List[str]]] = None
    """comma (',') delimited Min,Max range. Can set multiple time for multiple bands."""

    color_formula: Optional[str] = None
    """rio-color formula"""

    colormap: Optional[str] = None
    """JSON encoded custom Colormap"""

    colormap_name: Optional[str] = None
    """rio-tiler color map name"""

    return_mask: Optional[bool] = None
    """Add mask to the output data. Default is True"""

    buffer: Optional[float] = None
    """Add buffer on each side of the tile (e.g 0.5 = 257x257, 1.0 = 258x258)"""

    scan_limit: Optional[int] = None
    """Return as soon as we scan N items (defaults to 10000 in PgSTAC)"""

    items_limit: Optional[int] = None
    """Return as soon as we have N items per geometry (defaults to 100 in PgSTAC)"""

    time_limit: Optional[int] = None
    """Return after N seconds to avoid long requests (defaults to 5 in PgSTAC)"""

    exitwhenfull: Optional[bool] = None
    """Return as soon as the geometry is fully covered (defaults to True in PgSTAC)"""

    skipcovered: Optional[bool] = None
    """Skip any items that would show up completely under the previous items.

    Defaults to True in PgSTAC
    """

    @property
    def encoded_query_string(self) -> str:
        options = self.dict(
            exclude_defaults=True, exclude_none=True, exclude_unset=True
        )
        encoded_options: List[str] = []
        for key, value in options.items():
            if isinstance(value, list):
                for item in value:
                    encoded_options.append(f"{key}={quote(str(item))}")
            else:
                encoded_options.append(f"{key}={quote(str(value))}")
        encoded_options.append("tile_scale=2")
        return "&".join(encoded_options)

    @classmethod
    def from_query_params(cls, render_params: str) -> "RenderOptions":
        result: Dict[str, Any] = {}
        for p in render_params.split("&"):
            k, v = p.split("=")
            if k in result:
                if not isinstance(result[k], list):
                    result[k] = [result[k]]
                result[k].append(v)
            else:
                result[k] = v

        return RenderOptions(**result)


@attr.s
class RIOImage(ImageData):
    @property
    def size(self) -> Tuple[int, int]:
        return (self.width, self.height)

    def paste(
        self,
        img: "RIOImage",
        box: Optional[
            Union[
                Tuple[int, int],
                Tuple[int, int, int, int],
            ]
        ],
    ) -> None:
        if img.count != self.count:
            raise Exception("Cannot merge 2 images with different band number")

        if img.data.dtype != self.data.dtype:
            raise Exception("Cannot merge 2 images with different datatype")

        # Pastes another image into this image.
        # The box argument is either a 2-tuple giving the upper left corner,
        # a 4-tuple defining the left, upper, right, and lower pixel coordinate,
        # or None (same as (0, 0)). See Coordinate System. If a 4-tuple is given,
        # the size of the pasted image must match the size of the region.
        if box is None:
            box = (0, 0)

        if box:
            if len(box) == 2:
                minx, maxy = box  # type: ignore
                self.data[:, maxy:, minx:] = img.data
                self.mask[maxy:, minx:] = img.mask

            elif len(box) == 4:
                # TODO add more size tests
                minx, maxy, maxy, miny = box  # type: ignore
                self.data[:, maxy:miny, minx:maxy] = img.data
                self.mask[maxy:miny, minx:maxy] = img.mask

            else:
                raise Exception("Invalid box format")

    def crop(self, bbox: Tuple[int, int, int, int]) -> "RIOImage":
        """From rio-tiler 4.0"""
        col_min, row_min, col_max, row_max = bbox

        data = self.data[:, row_min:row_max, col_min:col_max]
        mask = self.mask[row_min:row_max, col_min:col_max]

        return RIOImage(  # type: ignore
            data,
            mask,
            assets=self.assets,
            crs=self.crs,
            bounds=BoundingBox(*bbox),
            band_names=self.band_names,
            metadata=self.metadata,
            # dataset_statistics=self.dataset_statistics,  # added in rio-tiler 4.0
        )

    # This is slightly different from the resize method in rio-tiler 4.0
    def resize(  # type: ignore
        self,
        size: Tuple[int, int],
        resampling_method: Resampling = "nearest",
    ) -> "RIOImage":
        """From rio-tiler 4.0"""
        width, height = size

        data = resize_array(self.data, height, width, resampling_method)
        mask = resize_array(self.mask, height, width, resampling_method)

        return RIOImage(  # type: ignore
            data,
            mask,
            assets=self.assets,
            crs=self.crs,
            bounds=self.bounds,
            band_names=self.band_names,
            metadata=self.metadata,
            # dataset_statistics=self.dataset_statistics,  # added in rio-tiler 4.0
        )

    @classmethod
    def from_rio(
        cls, dataset: Union[DatasetReader, DatasetWriter, MemoryFile]
    ) -> "RIOImage":
        indexes = non_alpha_indexes(dataset)

        if ColorInterp.alpha in dataset.colorinterp:
            # If dataset has an alpha band we need to get the mask using
            # the alpha band index and then split the data and mask values
            alpha_idx = dataset.colorinterp.index(ColorInterp.alpha) + 1
            idx = tuple(indexes) + (alpha_idx,)
            data = dataset.read(indexes=idx)
            data, mask = data[0:-1], data[-1].astype("uint8")

        else:
            data = dataset.read(indexes=indexes)
            mask = dataset.dataset_mask()

        return cls(  # type: ignore
            data,
            mask,
            crs=dataset.crs,
            bounds=dataset.bounds,
        )

    def statistics(
        self,
        categorical: bool = False,
        categories: Optional[List[float]] = None,
        percentiles: List[int] = [2, 98],
        hist_options: Optional[Dict] = None,
    ) -> Dict:
        data = numpy.ma.array(self.data)
        data.mask = self.mask == 0

        hist_options = hist_options or {}

        stats = get_array_statistics(
            data,
            categorical=categorical,
            categories=categories,
            percentiles=percentiles,
            **hist_options,
        )

        return {f"{self.band_names[ix]}": stats[ix] for ix in range(len(stats))}
