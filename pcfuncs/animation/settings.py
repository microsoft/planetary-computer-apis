import logging

from cachetools import Cache, LRUCache, cachedmethod
from funclib.settings import BaseExporterSettings

from .constants import (
    ANIMATION_SETTINGS_PREFIX,
    DEFAULT_ANIMATION_CONTAINER_URL,
    DEFAULT_CONCURRENCY,
)

logger = logging.getLogger(__name__)


class AnimationSettings(BaseExporterSettings):
    _cache: Cache = LRUCache(maxsize=100)

    output_storage_url: str = DEFAULT_ANIMATION_CONTAINER_URL
    tile_request_concurrency: int = DEFAULT_CONCURRENCY

    model_config = {
        "env_prefix": ANIMATION_SETTINGS_PREFIX,
        "env_nested_delimiter": "__",  # type: ignore
    }

    @classmethod
    @cachedmethod(lambda cls: cls._cache)
    def get(cls) -> "AnimationSettings":
        settings = AnimationSettings()  # type: ignore
        logger.info(f"API URL: {settings.api_root_url}")
        logger.info(f"Concurrency limit: {settings.tile_request_concurrency}")
        return settings
