from dataclasses import dataclass

from pyproj import Transformer

from .raster import Bbox


@dataclass
class Point:
    x: float
    y: float


def geop_to_imgp(
    geo_p: Point, bbox: Bbox, pixel_width: float, pixel_height: float
) -> Point:
    left: float = bbox.xmin
    top: float = bbox.ymax

    x: float = (geo_p.x - left) / ((bbox.xmax - bbox.xmin) / pixel_width)
    y: float = (top - geo_p.y) / ((bbox.ymax - bbox.ymin) / pixel_height)
    return Point(x, y)


to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
