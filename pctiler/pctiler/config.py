import os
from dataclasses import dataclass
from functools import lru_cache

from pydantic import BaseSettings

# Hostname to fetch STAC information from
STAC_API_URL_ENV_VAR = "STAC_API_URL"
# HREF base to be used when sending responses
STAC_API_HREF_ENV_VAR = "STAC_API_HREF"


@dataclass
class FeatureFlags:
    VRT: bool = True if os.environ.get("FF_VRT") else False


class Settings(BaseSettings):
    stac_api_url: str = os.environ[STAC_API_URL_ENV_VAR]
    stac_api_href: str = os.environ[STAC_API_HREF_ENV_VAR]

    title: str = "Preview of Tile Access Services"
    openapi_url: str = "/openapi.json"
    ogc_endpoint_prefix: str = "/asset-tiles"
    item_endpoint_prefix: str = "/item"
    collection_endpoint_prefix: str = "/collection"
    mosaic_endpoint_prefix: str = "/mosaic"
    legend_endpoint_prefix: str = "/legend"
    debug: bool = os.getenv("TILER_DEBUG", "False").lower() == "true"
    api_version: str = "1.0"

    feature_flags: FeatureFlags = FeatureFlags()


@lru_cache
def get_settings() -> Settings:
    return Settings()
