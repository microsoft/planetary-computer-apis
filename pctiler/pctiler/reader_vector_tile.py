import logging
import time
from typing import Optional

import planetary_computer as pc
import requests
from starlette.requests import Request

from pccommon.config.collections import VectorTileset
from pccommon.logging import get_custom_dimensions
from pctiler.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class VectorTileReader:
    """
    Load a vector tile from a storage account container and return
    """

    def __init__(self, collection: str, tileset: VectorTileset, request: Request):
        self.request = request
        self.tileset = tileset
        self.collection = collection

    def get_tile(self, z: int, x: int, y: int) -> Optional[bytes]:
        """
        Get a vector tile from a storage account container
        """
        blob_url = self._blob_url_for_tile(z, x, y)

        ts = time.perf_counter()
        response = requests.get(blob_url, stream=True)
        logger.info(
            "Perf: PBF upsteam load time",
            extra=get_custom_dimensions(
                {"duration": f"{time.perf_counter() - ts:0.4f}"}, self.request
            ),
        )

        if response.status_code == 404:
            return None

        if response.status_code != 200:
            raise Exception(f"Error loading tile {blob_url}")

        return response.raw.read()

    def _blob_url_for_tile(self, z: int, x: int, y: int) -> str:
        """
        Get the URL to the storage account container and blob
        """
        tile_url = (
            f"{settings.vector_tile_sa_base_url}"
            f"/{self.collection}"
            f"/{self.tileset.id}/{z}/{x}/{y}.pbf"
        )

        return pc.sign_url(tile_url)
