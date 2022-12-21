from typing import Dict, cast

import matplotlib
import numpy as np
from rio_tiler.types import ColorMapType, ColorTuple


def make_qpe_colormap() -> ColorMapType:
    qpe = matplotlib.colors.LinearSegmentedColormap.from_list(
        "qpe",
        [
            (0.000, "#00000000"),
            (0.003, "#1863b7"),
            (0.010, "#1863b7"),
            (0.011, "#30817e"),
            (0.025, "#30817e"),
            (0.026, "#419944"),
            (0.050, "#419944"),
            (0.051, "#5dac12"),
            (0.075, "#5dac12"),
            (0.076, "#94ba15"),
            (0.100, "#94ba15"),
            (0.101, "#c6c61e"),
            (0.150, "#c6c61e"),
            (0.151, "#f1cb24"),
            (0.200, "#f1cb24"),
            (0.201, "#fbb621"),
            (0.250, "#fbb621"),
            (0.251, "#f8981b"),
            (0.300, "#f8981b"),
            (0.301, "#f47916"),
            (0.400, "#f47916"),
            (0.401, "#f15a1e"),
            (0.500, "#f15a1e"),
            (0.501, "#fa605d"),
            (0.600, "#fa605d"),
            (0.601, "#ff79aa"),
            (0.800, "#ff79aa"),
            (0.801, "#fe92fb"),
            (1.000, "#fe92fb"),
        ],
        256,
    )
    ramp = np.linspace(0, 1, 256)
    cmap_vals = qpe(ramp)[:, :]
    cmap_uint8 = (cmap_vals * 255).astype("uint8")
    colormap = {
        idx: cast(ColorTuple, tuple(value)) for idx, value in enumerate(cmap_uint8)
    }
    return colormap


qpe_colormaps: Dict[str, ColorMapType] = {
    "qpe": make_qpe_colormap(),
}
