from typing import Dict
from rio_tiler.types import ColorMapType


mtbs_colormaps: Dict[str, ColorMapType] = {
    "mtbs-severity": {
        0: (0, 0, 0, 0),
        1: (0, 100, 0, 255),
        2: (127, 255, 212, 255),
        3: (255, 255, 0, 255),
        4: (255, 0, 0, 255),
        5: (127, 255, 0, 255),
        6: (255, 255, 255, 255),
    },
}
