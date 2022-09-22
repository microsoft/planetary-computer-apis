import logging
from typing import Optional

from azure.storage.blob import ContainerClient
from cachetools import Cache, LRUCache, cachedmethod
from pydantic import BaseSettings

from pccommon.blob import get_container_client

from .constants import (
    ANIMATION_SETTINGS_PREFIX,
    DEFAULT_ANIMATION_CONTAINER_URL,
    DEFAULT_CONCURRENCY,
)

logger = logging.getLogger(__name__)


class AnimationSettings(BaseSettings):
    _cache: Cache = LRUCache(maxsize=100)

    api_root_url: str = "https://planetarycomputer.microsoft.com/api/data/v1"
    output_storage_url: str = DEFAULT_ANIMATION_CONTAINER_URL
    output_sas: Optional[str] = None
    output_account_key: Optional[str] = None
    tile_request_concurrency: int = DEFAULT_CONCURRENCY

    resource_path = "/home/site/wwwroot/animation/resources"

    def get_container_client(self) -> ContainerClient:
        return get_container_client(
            self.output_storage_url,
            sas_token=self.output_sas,
            account_key=self.output_account_key,
        )

    class Config:
        env_prefix = ANIMATION_SETTINGS_PREFIX
        env_nested_delimiter = "__"

    @classmethod
    @cachedmethod(lambda cls: cls._cache)
    def get(cls) -> "AnimationSettings":
        settings = AnimationSettings()  # type: ignore
        logger.info(f"API URL: {settings.api_root_url}")
        logger.info(f"Concurrency limit: {settings.tile_request_concurrency}")
        return settings
