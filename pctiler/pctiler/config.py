import os
from dataclasses import dataclass
from functools import lru_cache

from pydantic import BaseSettings, Field

# Hostname to fetch STAC information from
STAC_API_URL_ENV_VAR = "STAC_API_URL"
# HREF base to be used when sending responses
STAC_API_HREF_ENV_VAR = "STAC_API_HREF"

DEFAULT_MAX_ITEMS_PER_TILE_ENV_VAR = "DEFAULT_MAX_ITEMS_PER_TILE"


@dataclass
class FeatureFlags:
    VRT: bool = True if os.environ.get("FF_VRT") else False


class Settings(BaseSettings):
    stac_api_url: str = os.environ[STAC_API_URL_ENV_VAR]
    stac_api_href: str = os.environ[STAC_API_HREF_ENV_VAR]

    title: str = "Preview of Tile Access Services"
    openapi_url: str = "/openapi.json"
    item_endpoint_prefix: str = "/item"
    mosaic_endpoint_prefix: str = "/mosaic"
    legend_endpoint_prefix: str = "/legend"
    debug: bool = os.getenv("TILER_DEBUG", "False").lower() == "true"
    api_version: str = "1.0"
    default_max_items_per_tile: int = Field(
        env=DEFAULT_MAX_ITEMS_PER_TILE_ENV_VAR, default=10
    )

    feature_flags: FeatureFlags = FeatureFlags()


@lru_cache
def get_settings() -> Settings:
    return Settings()
