import contextlib
import pathlib
import threading
import time
from enum import Enum
from types import DynamicClassAttribute
from typing import Dict, Generator

import pytest
import uvicorn
from fastapi import FastAPI, Path, Query
from funclib.models import RenderOptions
from funclib.tiles import GDALTileSet
from mercantile import Tile
from rio_tiler.io import Reader
from rio_tiler.profiles import img_profiles
from starlette.responses import Response

HERE = pathlib.Path(__file__).parent
DATA_FILES = HERE / ".." / "data-files"

cog_file = HERE / ".." / "data-files" / "cog.tif"


class ImageDriver(str, Enum):
    """Supported output GDAL drivers."""

    jpg = "JPEG"
    png = "PNG"
    tif = "GTiff"


class MediaType(str, Enum):
    """Responses Media types formerly known as MIME types."""

    tif = "image/tiff; application=geotiff"
    png = "image/png"
    jpeg = "image/jpeg"


class ImageType(str, Enum):
    """Available Output image type."""

    png = "png"
    tif = "tif"
    jpg = "jpg"

    @DynamicClassAttribute
    def profile(self) -> Dict:
        """Return rio-tiler image default profile."""
        return img_profiles.get(self._name_, {})

    @DynamicClassAttribute
    def driver(self) -> str:
        """Return rio-tiler image default profile."""
        return ImageDriver[self._name_].value

    @DynamicClassAttribute
    def mediatype(self) -> str:
        """Return image media type."""
        return MediaType[self._name_].value


class Server(uvicorn.Server):
    """Uvicorn Server."""

    def install_signal_handlers(self) -> None:
        """install handlers."""
        pass

    @contextlib.contextmanager
    def run_in_thread(self) -> Generator:
        """run in thread."""
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()


@pytest.fixture(scope="session")
def application() -> Generator:
    """Run app in Thread."""
    app = FastAPI()

    @app.get("/{z}/{x}/{y}.{format}", response_class=Response)
    def tiler(
        z: int = Path(...),
        x: int = Path(...),
        y: int = Path(...),
        format: ImageType = Path(...),
        collection: str = Query(...),
        tile_scale: int = Query(
            1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
        ),
    ) -> Response:
        with Reader(collection) as src:
            image = src.tile(x, y, z, tilesize=tile_scale * 256)

        content = image.render(
            img_format=format.driver,
            **format.profile,
        )
        return Response(content, media_type=format.mediatype)

    config = uvicorn.Config(
        app, host="127.0.0.1", port=5000, log_level="info", loop="asyncio"
    )
    server = Server(config=config)
    with server.run_in_thread():
        yield "http://127.0.0.1:5000"


async def test_app(application: str) -> None:
    """Test GDAL Tileset application."""
    tileset = GDALTileSet(
        f"{application}/{{z}}/{{x}}/{{y}}.tif",
        RenderOptions(
            collection=str(cog_file),
        ),
    )
    expect = f"http://127.0.0.1:5000/0/1/2.tif?collection={cog_file}&tile_scale=2"
    assert tileset.get_tile_url(0, 1, 2) == expect

    # Test one Tile
    url = tileset.get_tile_url(7, 44, 25)
    im = await tileset._get_tile(url)
    assert im
    assert im.width == 512
    assert im.height == 512

    # Test Mosaic
    mosaic = await tileset.get_mosaic([Tile(44, 25, 7), Tile(45, 25, 7)])
    assert mosaic.image.width == 1024
    assert mosaic.image.height == 512
    assert mosaic.image.count == 1  # same as cog_file
    assert mosaic.image.data.dtype == "uint16"  # same as cog_file
