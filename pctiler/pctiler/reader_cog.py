# type:ignore
# flake8:noqa
"""Overrides to COG reading by titiler/rio_tiler.

This file contains workarounds in the form of
overridden logic in order to make titiler/rio_tiler
work in certain cases.
Specifically, the GOES thumbnails would not render correctly
due to the WarpedVRT not being able to handle errors coming from
the custom CRS of those COGs.

TODO: Delete once moved to rasterio 1.3 (https://github.com/rasterio/rasterio/pull/2357)

"""
import math
import warnings
from typing import Any, Callable, Dict, Optional, Tuple, Union

import attr
import numpy
import rasterio
from rasterio import transform, windows
from rasterio.enums import Resampling
from rasterio.io import DatasetReader, DatasetWriter
from rasterio.vrt import WarpedVRT
from rio_tiler.constants import Indexes, NoData
from rio_tiler.errors import AlphaBandWarning, ExpressionMixingWarning
from rio_tiler.expression import apply_expression, parse_expression
from rio_tiler.io.stac import COGReader
from rio_tiler.models import ImageData
from rio_tiler.utils import non_alpha_indexes


def goes_thumbnail_read(
    src_dst: Union[DatasetReader, DatasetWriter, WarpedVRT],
    height: Optional[int] = None,
    width: Optional[int] = None,
    indexes: Optional[Indexes] = None,
    window: Optional[windows.Window] = None,
    force_binary_mask: bool = True,
    nodata: Optional[NoData] = None,
    unscale: bool = False,
    resampling_method: Resampling = Resampling.nearest,
    vrt_options: Optional[Dict] = None,
    post_process: Optional[
        Callable[[numpy.ndarray, numpy.ndarray], Tuple[numpy.ndarray, numpy.ndarray]]
    ] = None,
) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """Low level read function.

    Args:
        src_dst (rasterio.io.DatasetReader or rasterio.io.DatasetWriter or rasterio.vrt.WarpedVRT): Rasterio dataset.
        height (int, optional): Output height of the array.
        width (int, optional): Output width of the array.
        indexes (sequence of int or int, optional): Band indexes.
        window (rasterio.windows.Window, optional): Window to read.
        force_binary_mask (bool, optional): Cast returned mask to binary values (0 or 255). Defaults to `True`.
        nodata (int or float, optional): Overwrite dataset internal nodata value.
        unscale (bool, optional): Apply 'scales' and 'offsets' on output data value. Defaults to `False`.
        resampling_method (rasterio.enums.Resampling, optional): Rasterio's resampling algorithm. Defaults to `nearest`.
        vrt_options (dict, optional): Options to be passed to the rasterio.warp.WarpedVRT class.
        post_process (callable, optional): Function to apply on output data and mask values.

    Returns:
        tuple: Data (numpy.ndarray) and Mask (numpy.ndarray) values.

    """
    # OVERRIDE: Set indexes manually so they don't get checked
    # if isinstance(indexes, int):
    #     indexes = (indexes,)
    indexes = (1,)

    vrt_params = dict(add_alpha=True, resampling=Resampling[resampling_method])
    nodata = nodata if nodata is not None else src_dst.nodata
    if nodata is not None:
        vrt_params.update(dict(nodata=nodata, add_alpha=False, src_nodata=nodata))

    # OVERRIDE: Getting the alpha band raises an error on GOES
    # if has_alpha_band(src_dst):
    #     vrt_params.update(dict(add_alpha=False))

    if indexes is None:
        indexes = non_alpha_indexes(src_dst)
        if indexes != src_dst.indexes:
            warnings.warn(
                "Alpha band was removed from the output data array", AlphaBandWarning
            )

    out_shape = (len(indexes), height, width) if height and width else None
    mask_out_shape = (height, width) if height and width else None
    resampling = Resampling[resampling_method]

    if vrt_options:
        vrt_params.update(vrt_options)

    # OVERRIDE - don't use a WarpedVRT or else it fails with GOES.
    data = src_dst.read(
        indexes=indexes,
        window=window,
        out_shape=out_shape,
        resampling=resampling,
    )
    mask = src_dst.dataset_mask(
        window=window,
        out_shape=mask_out_shape,
        resampling=resampling,
    )

    if force_binary_mask:
        mask = numpy.where(mask != 0, numpy.uint8(255), numpy.uint8(0))

    if unscale:
        data = data.astype("float32", casting="unsafe")
        numpy.multiply(data, src_dst.scales[0], out=data, casting="unsafe")
        numpy.add(data, src_dst.offsets[0], out=data, casting="unsafe")

    if post_process:
        data, mask = post_process(data, mask)

    return data, mask


def goes_thumbnail_preview(
    src_dst: Union[DatasetReader, DatasetWriter, WarpedVRT],
    max_size: int = 1024,
    height: int = None,
    width: int = None,
    **kwargs: Any,
) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """Read decimated version of a dataset.

    Args:
        src_dst (rasterio.io.DatasetReader or rasterio.io.DatasetWriter or rasterio.vrt.WarpedVRT): Rasterio dataset.
        max_size (int, optional): Limit output size array if not widht and height. Defaults to `1024`.
        height (int, optional): Output height of the array.
        width (int, optional): Output width of the array.
        kwargs (optional): Additional options to forward to `rio_tiler.reader.read`.

    Returns:
        tuple: Data (numpy.ndarray) and Mask (numpy.ndarray) values.

    """
    if not height and not width:
        if max(src_dst.height, src_dst.width) < max_size:
            height, width = src_dst.height, src_dst.width
        else:
            ratio = src_dst.height / src_dst.width
            if ratio > 1:
                height = max_size
                width = math.ceil(height / ratio)
            else:
                width = max_size
                height = math.ceil(width * ratio)

    return goes_thumbnail_read(src_dst, height, width, **kwargs)


class CustomCOGReader(COGReader):
    """Custom COG reader.

    A couple of workarounds:

    GOES projection: A hack to get GOES thumbnails to appear, which fail with a "tolerance error"
    when using the default logic. For the GOES case this doesn't use a WarpedVRT,
    which avoids that error.

    Sentinel 1 GRD: These use GCPs, which are not supported by default in the COGReader.
    """

    # dataset is not a input option.
    dataset: Union[DatasetReader, DatasetWriter, WarpedVRT] = attr.ib(init=False)

    def __attrs_post_init__(self):
        """Define _kwargs, open dataset and get info."""
        if "sentinel1euwest.blob.core.windows.net" in self.input:
            self.src_dataset = self._ctx_stack.enter_context(rasterio.open(self.input))
            self.dataset = self._ctx_stack.enter_context(
                WarpedVRT(
                    self.src_dataset,
                    src_crs=self.src_dataset.gcps[1],
                    src_transform=transform.from_gcps(self.src_dataset.gcps[0]),
                )
            )
        super().__attrs_post_init__()

    def preview_goes(
        self,
        indexes: Optional[Indexes] = None,
        expression: Optional[str] = None,
        **kwargs: Any,
    ) -> ImageData:
        """Return a preview of a COG. (Custom hack for GOES)

        Args:
            indexes (sequence of int or int, optional): Band indexes.
            expression (str, optional): rio-tiler expression (e.g. b1/b2+b3).
            kwargs (optional): Options to forward to the `rio_tiler.reader.preview` function.

        Returns:
            rio_tiler.models.ImageData: ImageData instance with data, mask and input spatial info.

        """
        kwargs = {**self._kwargs, **kwargs}

        if isinstance(indexes, int):
            indexes = (indexes,)

        if indexes and expression:
            warnings.warn(
                "Both expression and indexes passed; expression will overwrite indexes parameter.",
                ExpressionMixingWarning,
            )

        if expression:
            indexes = parse_expression(expression)

        data, mask = goes_thumbnail_preview(self.dataset, indexes=indexes, **kwargs)

        if expression and indexes:
            blocks = expression.lower().split(",")
            bands = [f"b{bidx}" for bidx in indexes]
            data = apply_expression(blocks, bands, data)

        return ImageData(
            data,
            mask,
            bounds=self.dataset.bounds,
            crs=self.dataset.crs,
            assets=[self.input],
        )

    def preview(
        self,
        indexes: Optional[Indexes] = None,
        expression: Optional[str] = None,
        **kwargs: Any,
    ) -> ImageData:
        """Return a preview of a COG.

        Args:
            indexes (sequence of int or int, optional): Band indexes.
            expression (str, optional): rio-tiler expression (e.g. b1/b2+b3).
            kwargs (optional): Options to forward to the `rio_tiler.reader.preview` function.

        Returns:
            rio_tiler.models.ImageData: ImageData instance with data, mask and input spatial info.

        """
        if "goeseuwest.blob.core.windows.net" in self.input:
            return self.preview_goes(indexes, expression, **kwargs)

        return super().preview(indexes, expression, **kwargs)
