import os
from functools import lru_cache

from pydantic import BaseSettings

API_VERSION = "1.1"

API_LANDING_PAGE_ID = "microsoft-pc"
API_TITLE = "Microsoft Planetary Computer STAC API"
API_DESCRIPTION = (
    "Searchable spatiotemporal metadata describing Earth science datasets "
    "hosted by the Microsoft Planetary Computer"
)
API_CONFORMANCE_CLASSES = [
    "https://api.stacspec.org/v1.0.0-beta.2/core",
    "https://api.stacspec.org/v1.0.0-beta.2/item-search",
    "https://api.stacspec.org/v1.0.0-beta.2/item-search#query",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
]

TILER_HREF_ENV_VAR = "TILER_HREF"


class Settings(BaseSettings):
    tiler_href: str = os.environ[TILER_HREF_ENV_VAR]
    openapi_url: str = "/openapi.json"
    pc_collections_prefix: str = "/collections"
    debug: bool = os.getenv("PQE_DEBUG", "False").lower() == "true"
    api_version: str = "v1.1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
