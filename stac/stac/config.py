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
    "https://api.stacspec.org/v1.0.0-beta.3/core",
    "https://api.stacspec.org/v1.0.0-beta.3/item-search",
    "https://api.stacspec.org/v1.0.0-beta.3/item-search#query",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
]

TILER_HREF_ENV_VAR = "TILER_HREF"


class Settings(BaseSettings):
    """Class for specifying application parameters

    ...

    Attributes
    ----------
    tiler_href : str
        URL root for tiling endpoints
    openapi_url : str
        relative path to JSON document which describes the application's API
    debug : bool
        flag directing the application to operate in debugging mode
    api_version : str
        version of application
    """

    tiler_href: str = os.environ.get("TILER_HREF_ENV_VAR", "")
    openapi_url: str = "/openapi.json"
    debug: bool = os.getenv("PQE_DEBUG", "False").lower() == "true"
    api_version: str = "v1.1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
