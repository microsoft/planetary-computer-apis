from io import BytesIO

from fastapi import APIRouter, HTTPException
from starlette.responses import Response
from matplotlib.colors import ListedColormap
from rio_tiler.colormap import make_lut

import matplotlib.pyplot as plt
import numpy as np

from ..colormaps import custom_colormaps, registered_cmaps

legend_router = APIRouter()


@legend_router.get("/colormap/{cmap_name}", response_class=Response)
async def get_legend(
    cmap_name: str, height: float = 0.15, width: float = 5, trim_end: int = 0
):
    """Generate a legend image for a given colormap."""
    if registered_cmaps.get(cmap_name) is None:
        raise HTTPException(status_code=404, detail=f"Colormap {cmap_name} not found")

    img = make_colormap_image(cmap_name, height, width, trim_end)

    return Response(content=img.read(), media_type="image/jpg")


@legend_router.get("/classmap/{classmap_name}")
async def get_classmap_legend(classmap_name: str):
    """Generate labels and color swatches for a given classmap."""
    classmap = custom_colormaps.get(classmap_name)
    if classmap is None:
        raise HTTPException(
            status_code=404, detail=f"Classmap {classmap_name} not found"
        )

    return Response(classmap, media_type="application/json")


def make_colormap_image(cmap_name: str, height: int, width: int, trim_end: int):
    """Generate a color gradient image for a given colormap."""
    _, ax = plt.subplots(nrows=1, figsize=(width, height))

    is_custom = cmap_name in custom_colormaps
    length = len(custom_colormaps[cmap_name]) if is_custom else 255
    length = min(length, 255) - trim_end

    gradient = np.linspace(0, 1, length + 1)
    gradient = np.vstack((gradient, gradient))

    ax.imshow(gradient, aspect="auto", cmap=make_colormap(cmap_name, length))
    ax.set_axis_off()

    img = BytesIO()
    plt.savefig(img, pad_inches=0, bbox_inches="tight", transparent=False)
    img.seek(0)
    return img


def make_colormap(name: str, length: int):
    """Use registered rio-tiler colormaps to create matplotlib colormap"""
    colors = make_lut(registered_cmaps.get(name))
    colors = colors[0 : length + 1]
    # rescale to 0-1
    return ListedColormap(colors / 256, name=name, N=length)
