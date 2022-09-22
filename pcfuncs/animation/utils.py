import io
import os
from dataclasses import dataclass
from uuid import uuid4

import mercantile
from pyproj import Transformer

from .settings import AnimationSettings


@dataclass
class Point:
    x: float
    y: float


def geop_to_imgp(
    geo_p: Point, bbox: mercantile.Bbox, pixel_width: float, pixel_height: float
) -> Point:
    left: float = bbox.left
    top: float = bbox.top

    x: float = (geo_p.x - left) / ((bbox.right - bbox.left) / pixel_width)
    y: float = (top - geo_p.y) / ((bbox.top - bbox.bottom) / pixel_height)
    return Point(x, y)


to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)


def upload_gif(gif: io.BytesIO, collection_name: str) -> str:
    settings = AnimationSettings.get()
    filename = f"planetarycomputer-{collection_name}-{uuid4().hex[:14]}.gif"
    blob_url = os.path.join(settings.output_storage_url, filename)
    with settings.get_container_client() as container_client:
        gif.seek(0)
        container_client.upload_blob(name=filename, data=gif)

    return blob_url
