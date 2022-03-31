from typing import Dict, cast

import matplotlib
import numpy as np
from rio_tiler.types import ColorMapType, ColorTuple


def make_biomass_colormap() -> ColorMapType:
    biomass = matplotlib.colors.LinearSegmentedColormap.from_list(
        "chloris-biomass",
        [
            "#c6c875",
            "#77a865",
            "#3d8757",
            "#29583a",
            "#2e3926",
            "#050603",
        ],
        256,
    )
    ramp = np.linspace(0, 1, 256)
    cmap_vals = biomass(ramp)[:, :]
    cmap_uint8 = (cmap_vals * 255).astype("uint8")
    colormap = {
        idx: cast(ColorTuple, tuple(value)) for idx, value in enumerate(cmap_uint8)
    }
    return colormap


chloris_colormaps: Dict[str, ColorMapType] = {
    "chloris-biomass": make_biomass_colormap(),
}
