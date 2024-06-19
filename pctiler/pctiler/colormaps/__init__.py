from typing import Dict

from rio_tiler.colormap import cmap
from rio_tiler.types import ColorMapType
from titiler.core.dependencies import create_colormap_dependency

from .alos_palsar_mosaic import alos_palsar_mosaic_colormaps
from .chloris import chloris_colormaps
from .io_bii import io_bii_colormaps
from .jrc import jrc_colormaps
from .lidarusgs import lidar_colormaps
from .lulc import lulc_colormaps
from .modis import modis_colormaps
from .mtbs import mtbs_colormaps
from .noaa_c_cap import noaa_c_cap_colormaps
from .qpe import qpe_colormaps
from .viirs import viirs_colormaps

################################################################################
# Custom ColorMap Query Parameter Support
# The use of enums requires us to roll our own RenderParams dependency type
# if we want documentation on par with the default RenderParams class
################################################################################
registered_cmaps = cmap
custom_colormaps: Dict[str, ColorMapType] = {
    **io_bii_colormaps,
    **jrc_colormaps,
    **lulc_colormaps,
    **modis_colormaps,
    **mtbs_colormaps,
    **lidar_colormaps,
    **chloris_colormaps,
    **noaa_c_cap_colormaps,
    **alos_palsar_mosaic_colormaps,
    **qpe_colormaps,
    **viirs_colormaps,
}

for k, v in custom_colormaps.items():
    registered_cmaps = registered_cmaps.register({k: v})


PCColorMapParams = create_colormap_dependency(registered_cmaps)

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
