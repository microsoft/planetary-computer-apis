import logging
from typing import Optional

from azure.storage.blob import ContainerClient
from cachetools import Cache, LRUCache, cachedmethod
from pydantic import BaseSettings, validator

from pccommon.blob import get_container_client

from .constants import (
    ANIMATION_SETTINGS_PREFIX,
    DEFAULT_ANIMATION_CONTAINER_URL,
    MAX_CONCURRENCY,
)

logger = logging.getLogger(__name__)


class AnimationSettings(BaseSettings):
    _cache: Cache = LRUCache(maxsize=100)

    api_root_url: str = "https://planetarycomputer.microsoft.com/api/data/v1"
    output_storage_url: str = DEFAULT_ANIMATION_CONTAINER_URL
    output_sas: Optional[str] = None
    output_account_key: Optional[str] = None
    tile_request_concurrency: int = 10

    def get_container_client(self) -> ContainerClient:
        return get_container_client(
            self.output_storage_url,
            sas_token=self.output_sas,
            account_key=self.output_account_key,
        )

    @validator("tile_request_concurrency")
    def _validate_concurrency(cls, v: int) -> int:
        if v > MAX_CONCURRENCY:
            raise ValueError(f"tile_request_concurrency must be <= {MAX_CONCURRENCY}")
        return v

    class Config:
        env_prefix = ANIMATION_SETTINGS_PREFIX
        env_nested_delimiter = "__"

    @classmethod
    @cachedmethod(lambda cls: cls._cache)
    def get(cls) -> "AnimationSettings":
        import os

        logger.info(f"DEBUG: {os.environ.get('ANIMATION_CONTAINER_ACCOUNT_KEY')}")
        settings = AnimationSettings()  # type: ignore
        logger.info(f"API URL: {settings.api_root_url}")
        logger.info(f"Concurrency limit: {settings.tile_request_concurrency}")
        return settings
