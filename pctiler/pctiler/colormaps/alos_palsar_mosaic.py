from typing import Dict

from rio_tiler.types import ColorMapType


alos_palsar_mosaic_colormaps: Dict[str, ColorMapType] = {
    "alos-palsar-mask": {
        {
            0: (0, 0, 0),
            50: (0, 0, 255),
            100: (168, 168, 0),
            150: (0, 84, 84),
            255: (168, 153, 135),
        }
    },
}
