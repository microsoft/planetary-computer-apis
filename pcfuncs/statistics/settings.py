import logging

from cachetools import Cache, LRUCache, cachedmethod
from funclib.settings import BaseExporterSettings

from .constants import (
    DEFAULT_CONCURRENCY,
    DEFAULT_STATISTICS_CONTAINER_URL,
    STATISTICS_SETTINGS_PREFIX,
)

logger = logging.getLogger(__name__)


class StatisticsSettings(BaseExporterSettings):
    _cache: Cache = LRUCache(maxsize=100)

    output_storage_url: str = DEFAULT_STATISTICS_CONTAINER_URL
    tile_request_concurrency: int = DEFAULT_CONCURRENCY

    class Config:
        env_prefix = STATISTICS_SETTINGS_PREFIX
        env_nested_delimiter = "__"

    @classmethod
    @cachedmethod(lambda cls: cls._cache)
    def get(cls) -> "StatisticsSettings":
        settings = StatisticsSettings()  # type: ignore
        logger.info(f"API URL: {settings.api_root_url}")
        logger.info(f"Concurrency limit: {settings.tile_request_concurrency}")
        return settings
