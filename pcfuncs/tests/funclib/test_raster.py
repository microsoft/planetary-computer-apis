from pathlib import Path

from funclib.models import RIOImage
from funclib.raster import Bbox, GDALRaster, PILRaster, RasterExtent
from PIL import Image

HERE = Path(__file__).parent
DATA_FILES = HERE / ".." / "data-files"


def test_pil_crop() -> None:
    img = Image.open(DATA_FILES / "s2.png")
    raster = PILRaster(
        extent=RasterExtent(
            bbox=Bbox(0, 0, 10, 10),
            cols=img.size[0],
            rows=img.size[1],
        ),
        image=img,
    )

    cropped = raster.crop(Bbox(0, 0, 5, 5))

    assert abs(cropped.extent.cols - (img.size[0] / 2)) < 1
    assert abs(cropped.extent.rows - (img.size[1] / 2)) < 1


def test_raster_extent_map_to_grid() -> None:
    extent = RasterExtent(
        bbox=Bbox(0, 0, 10, 10),
        cols=10,
        rows=10,
    )

    x, y = extent.map_to_grid(5, 5)

    assert x == 5
    assert y == 5


def test_rio_crop() -> None:
    with open(DATA_FILES / "s2.png", "rb") as src:
        img = RIOImage.from_bytes(src.read())

    raster = GDALRaster(
        extent=RasterExtent(
            bbox=Bbox(0, 0, 10, 10),
            cols=img.size[0],
            rows=img.size[1],
        ),
        image=img,
    )

    cropped = raster.crop(Bbox(0, 0, 5, 5))

    assert abs(cropped.extent.cols - (img.size[0] / 2)) < 1
    assert abs(cropped.extent.rows - (img.size[1] / 2)) < 1
