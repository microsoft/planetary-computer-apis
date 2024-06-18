import logging

from cachetools import LRUCache, cached
from funclib.settings import BaseExporterSettings


IMAGE_SETTINGS_PREFIX = "IMAGE_"
DEFAULT_CONCURRENCY = 10

logger = logging.getLogger(__name__)


class ImageSettings(BaseExporterSettings):
    # _cache: Cache = LRUCache(maxsize=100)

    tile_request_concurrency: int = DEFAULT_CONCURRENCY

    # Maximum tiles to fetch for a single request
    max_tile_count: int = 144
    max_pixels: int = 144 * 512 * 512

    model_config = {
        "env_prefix": IMAGE_SETTINGS_PREFIX,
        "env_nested_delimiter": "__",  # type: ignore
    }

    # @classmethod
    # @cachedmethod(lambda cls: cls._cache)
    # def get(cls) -> "ImageSettings":
    #     settings = ImageSettings()  # type: ignore
    #     logger.info(f"API URL: {settings.api_root_url}")
    #     logger.info(f"Concurrency limit: {settings.tile_request_concurrency}")
    #     return settings


@cached(LRUCache(maxsize=100))  # type: ignore
def get_settings() -> ImageSettings:
    settings = ImageSettings()  # type: ignore
    logger.info(f"API URL: {settings.api_root_url}")
    logger.info(f"Concurrency limit: {settings.tile_request_concurrency}")
    return settings
