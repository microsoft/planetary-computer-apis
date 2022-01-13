from enum import Enum
from typing import Dict, Optional

from fastapi import Query
from rio_tiler.colormap import cmap
from rio_tiler.types import ColorMapType
from titiler.core.dependencies import ColorMapParams

from .chloris import chloris_colormaps
from .jrc import jrc_colormaps
from .lulc import lulc_colormaps
from .mtbs import mtbs_colormaps
from .noaa_c_cap import noaa_c_cap_colormaps

################################################################################
# Custom ColorMap Query Parameter Support
# The use of enums requires us to roll our own RenderParams dependency type
# if we want documentation on par with the default RenderParams class
################################################################################
registered_cmaps = cmap
custom_colormaps: Dict[str, ColorMapType] = {
    **jrc_colormaps,
    **lulc_colormaps,
    **mtbs_colormaps,
    **chloris_colormaps,
    **noaa_c_cap_colormaps,
}

for k, v in custom_colormaps.items():
    registered_cmaps = registered_cmaps.register({k: v})

PCColorMapNames = Enum(  # type: ignore
    "ColorMapNames", [(a, a) for a in sorted(registered_cmaps.list())]
)


def PCColorMapParams(
    colormap_name: PCColorMapNames = Query(None, description="Colormap name"),
    colormap: str = Query(None, description="JSON encoded custom Colormap"),
) -> Optional[ColorMapType]:
    if colormap_name:
        cm = custom_colormaps.get(colormap_name.value)
        if cm:
            return cm
    return ColorMapParams(colormap_name, colormap)


# Placeholder for non-discrete range colormaps (unsupported)
# "hgb-above": {
#     0: [225, 252, 238, 255],
#     0.1: [220, 245, 233, 255],
#     0.2: [200, 230, 212, 255],
#     0.4: [182, 217, 194, 255],
#     0.8: [161, 201, 173, 255],
#     1.5: [143, 189, 155, 255],
#     3: [127, 176, 139, 255],
#     6: [109, 163, 122, 255],
#     12.5: [93, 150, 107, 255],
#     25: [77, 138, 90, 255],
#     50: [62, 125, 77, 255],
#     100: [47, 112, 62, 255],
#     200: [34, 102, 51, 255],
#     3000: [34, 102, 51, 255],
# },
