from typing import Dict

from rio_tiler.types import ColorMapType

alos_palsar_mosaic_colormaps: Dict[str, ColorMapType] = {
    "alos-palsar-mask": {
        0: (0, 0, 0, 0),
        50: (0, 0, 255, 255),
        100: (168, 168, 0, 255),
        150: (0, 84, 84, 255),
        255: (168, 153, 135, 255),
    },
    "alos-fnf": {
        0: (0, 0, 0, 255),  # nodata
        1: (0, 178, 0, 255),  # forest (> 90% canopy cover)
        2: (131, 239, 98, 255),  # forest (10-90% canopy coer)
        3: (255, 255, 153, 255),  # no-forest
        4: (0, 0, 255, 255),  # water
    },
}
