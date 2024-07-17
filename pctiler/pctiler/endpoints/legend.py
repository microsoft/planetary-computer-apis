# NOTE: we now have https://developmentseed.org/titiler/endpoints/colormaps/ in titiler

from io import BytesIO
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from matplotlib.colors import ListedColormap
from rio_tiler.colormap import make_lut

from ..colormaps import custom_colormaps, registered_cmaps

legend_router = APIRouter()


@legend_router.get("/interval/{classmap_name}", response_class=JSONResponse)
async def get_interval_legend(
    classmap_name: str,
    trim_start: int = 0,
    trim_end: int = 0,
) -> JSONResponse:
    """Generate values and color swatches mapping for a given interval classmap.

    Args:
        trim_start (int, optional): Number of items to trim from the start of the cmap
        trim_end (int, optional): Number of items to trim from the end of the cmap
    """
    classmap = custom_colormaps.get(classmap_name)

    if classmap is None:
        raise HTTPException(
            status_code=404, detail=f"Classmap {classmap_name} not found"
        )

    if type(classmap) is not list:
        raise HTTPException(
            status_code=400, detail=f"Classmap {classmap_name} is not an interval type"
        )

    trimmed_map = classmap[trim_start : len(classmap) - trim_end]  # type: ignore

    return JSONResponse(content=trimmed_map)


@legend_router.get("/classmap/{classmap_name}", response_class=JSONResponse)
async def get_classmap_legend(
    classmap_name: str,
    trim_start: int = 0,
    trim_end: int = 0,
) -> JSONResponse:
    """Generate values and color swatches mapping for a given classmap.

    Args:
        trim_start (int, optional): Number of items to trim from the start of the cmap
        trim_end (int, optional): Number of items to trim from the end of the cmap
    """
    classmap = custom_colormaps.get(classmap_name)

    if classmap is None:
        raise HTTPException(
            status_code=404, detail=f"Classmap {classmap_name} not found"
        )

    if type(classmap) is not dict:
        raise HTTPException(
            status_code=400, detail=f"Classmap {classmap_name} is not a classmap type"
        )

    keys = list(classmap.keys())  # type: ignore
    trimmed_keys = keys[trim_start : len(keys) - trim_end]
    trimmed_map = {k: classmap[k] for k in trimmed_keys}

    return JSONResponse(content=trimmed_map)


@legend_router.get("/colormap/{cmap_name}", response_class=Response)
async def get_legend(
    cmap_name: str,
    height: float = 0.15,
    width: float = 5,
    trim_start: int = 0,
    trim_end: int = 0,
) -> Response:
    """Generate a legend image for a given colormap.

    If the colormap has non-contiguous values at the beginning or end,
    which aren't desired in the output image, they can be trimmed by specifying
    the number of values to trim.

    Args:
        cmap_name (string): The name of the registered colormap to generate a legend for
        height (float, optional): The output height of the legend image
        width (float, optional): The output width of the legend image
        trim_start (int, optional): Number of items to trim from the start of the cmap
        trim_end (int, optional): Number of items to trim from the end of the cmap

    Returns:
        HTTP response with jpeg encoded image data
    """
    if registered_cmaps.get(cmap_name) is None:
        raise HTTPException(status_code=404, detail=f"Colormap {cmap_name} not found")

    img = make_colormap_image(cmap_name, height, width, trim_start, trim_end)

    return Response(content=img.read(), media_type="image/jpg")


def make_colormap_image(
    cmap_name: str, height: float, width: float, trim_start: int, trim_end: int
) -> BytesIO:
    """Generate a color gradient image for a given colormap."""

    # Setup the drawing canvas
    _, ax = plt.subplots(nrows=1, figsize=(width, height))

    # Determine the number of color entries, allowing for items to be trimmed
    # from the begining and end of the colormap
    is_custom = cmap_name in custom_colormaps
    length = len(custom_colormaps[cmap_name]) if is_custom else 255
    adjusted_length = min(length, 255) - trim_end - trim_start

    # Create a gradient array from 0 to 1 at the desired length, and a matplotlib
    # colormap representation of the specified colormap
    gradient = np.linspace(0, 1, adjusted_length + 1)
    gradient = np.vstack((gradient, gradient))
    cmap = make_colormap(cmap_name, trim_start, adjusted_length)

    # Draw the gradient on the canvas with no hash marks
    ax.set_axis_off()
    ax.imshow(
        gradient,
        aspect="auto",
        cmap=cmap,
    )

    # Save the image to a buffer with no additional padding on the canvas
    img = BytesIO()
    plt.savefig(img, pad_inches=0, bbox_inches="tight", transparent=False)
    img.seek(0)

    return img


def make_colormap(name: str, trim_start: int, length: int) -> ListedColormap:
    """Use registered rio-tiler colormaps to create matplotlib colormap"""
    cm = registered_cmaps.get(name)

    # Make sure we can use `make_lut`
    # see: https://github.com/cogeotiff/rio-tiler/blob/master/rio_tiler/colormap.py#L98-L108  # noqa
    if isinstance(cm, Sequence):
        raise Exception("Cannot make a colormap from Intervals colormap")

    if len(cm) > 256 or max(cm) >= 256:
        raise Exception("Cannot make a colormap for discrete colormap")

    colors = make_lut(cm)

    colors = colors[trim_start : length + 1]
    # rescale to 0-1
    return ListedColormap(colors / 256, name=name, N=length)
