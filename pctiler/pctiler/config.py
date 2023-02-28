import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urljoin

from fastapi import Request
from pydantic import BaseSettings, Field

# Hostname to fetch STAC information from
STAC_API_URL_ENV_VAR = "STAC_API_URL"
# HREF base to be used when sending responses
STAC_API_HREF_ENV_VAR = "STAC_API_HREF"

DEFAULT_MAX_ITEMS_PER_TILE_ENV_VAR = "DEFAULT_MAX_ITEMS_PER_TILE"
REQUEST_TIMEOUT_ENV_VAR = "REQUEST_TIMEOUT"
VECTORTILE_SA_BASE_URL_ENV_VAR = "VECTORTILE_SA_BASE_URL"


@dataclass
class FeatureFlags:
    VRT: bool = True if os.environ.get("FF_VRT") else False


class Settings(BaseSettings):
    stac_api_url: str = os.environ[STAC_API_URL_ENV_VAR]
    """Internal URL to access the STAC API"""

    stac_api_href: str = os.environ[STAC_API_HREF_ENV_VAR]
    """Public URL to access the STAC API.

    If relative, will use the request's base URL to generate the
    full HREF.
    """

    title: str = "Preview of Tile Access Services"
    openapi_url: str = "/openapi.json"
    item_endpoint_prefix: str = "/item"
    mosaic_endpoint_prefix: str = "/mosaic"
    legend_endpoint_prefix: str = "/legend"
    zarr_endpoint_prefix: str = "/zarr"
    vector_tile_endpoint_prefix: str = "/vector"
    vector_tile_sa_base_url: str = Field(env=VECTORTILE_SA_BASE_URL_ENV_VAR)

    debug: bool = os.getenv("TILER_DEBUG", "False").lower() == "true"
    api_version: str = "1.0"
    default_max_items_per_tile: int = Field(
        env=DEFAULT_MAX_ITEMS_PER_TILE_ENV_VAR, default=10
    )
    request_timout: int = Field(env=REQUEST_TIMEOUT_ENV_VAR, default=30)

    feature_flags: FeatureFlags = FeatureFlags()

    def get_stac_api_href(self, request: Request) -> str:
        """Generates the STAC API HREF.

        If the setting for the stac_api_href
        is relative, then use the request's base URL to generate the
        absolute URL.
        """
        if request:
            base_hostname = f"{request.url.scheme}://{request.url.netloc}/"
            return urljoin(base_hostname, self.stac_api_href)
        else:
            return self.stac_api_href


@lru_cache
def get_settings() -> Settings:
    return Settings()
