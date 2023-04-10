from typing import Dict, cast

import matplotlib
import numpy as np
from rio_tiler.types import ColorMapType, ColorTuple


def make_io_bii_colormap() -> ColorMapType:
    io_bii = matplotlib.colors.LinearSegmentedColormap.from_list(
        "io_bii",
        [
            (0.0, "#72736c"),
            (0.2, "#ccd3c5"),
            (0.4, "#cceaa2"),
            (0.6, "#69be72"),
            (0.8, "#309d53"),
            (1.0, "#006a37"),
        ],
        256,
    )
    ramp = np.linspace(0, 1, 256)
    cmap_vals = io_bii(ramp)[:, :]
    cmap_uint8 = (cmap_vals * 255).astype("uint8")
    colormap = {
        idx: cast(ColorTuple, tuple(value)) for idx, value in enumerate(cmap_uint8)
    }
    return colormap


io_bii_colormaps: Dict[str, ColorMapType] = {
    "io-bii": make_io_bii_colormap(),
}
