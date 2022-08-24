import logging
import os
from typing import Optional

from azure.storage.blob import ContainerClient
from cachetools import Cache, LRUCache, cachedmethod
from pydantic import BaseSettings

from pccommon.blob import get_container_client

IMAGE_SETTINGS_PREFIX = "IMAGE_"
DEFAULT_CONCURRENCY = 10

logger = logging.getLogger(__name__)


class ImageSettings(BaseSettings):
    _cache: Cache = LRUCache(maxsize=100)

    api_root_url: str = "https://planetarycomputer.microsoft.com/api/data/v1"
    output_storage_url: str
    output_sas: Optional[str] = None
    output_account_key: Optional[str] = None
    tile_request_concurrency: int = DEFAULT_CONCURRENCY

    # Maximum tiles to fetch for a single request
    max_tile_count: int = 144
    max_pixels: int = 144 * 512 * 512

    def get_container_client(self) -> ContainerClient:
        return get_container_client(
            self.output_storage_url,
            sas_token=self.output_sas,
            account_key=self.output_account_key,
        )

    def get_register_url(self, data_api_url_override: Optional[str] = None) -> str:
        return os.path.join(
            data_api_url_override or self.api_root_url, "mosaic/register/"
        )

    def get_mosaic_info_url(
        self, collection_id: str, data_api_url_override: Optional[str] = None
    ) -> str:
        return os.path.join(
            data_api_url_override or self.api_root_url,
            f"mosaic/info?collection={collection_id}",
        )

    class Config:
        env_prefix = IMAGE_SETTINGS_PREFIX
        env_nested_delimiter = "__"

    @classmethod
    @cachedmethod(lambda cls: cls._cache)
    def get(cls) -> "ImageSettings":
        settings = ImageSettings()  # type: ignore
        logger.info(f"API URL: {settings.api_root_url}")
        logger.info(f"Concurrency limit: {settings.tile_request_concurrency}")
        return settings
