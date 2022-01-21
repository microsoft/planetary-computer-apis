import os
from functools import lru_cache

from pydantic import BaseSettings
from stac_fastapi.extensions.core import (
    FieldsExtension,
    FilterExtension,
    QueryExtension,
    SortExtension,
    TokenPaginationExtension,
)
from stac_fastapi.extensions.core.filter.filter import FilterConformanceClasses

API_VERSION = "1.1"
STAC_API_VERSION = "v1.0.0-beta.4"

API_LANDING_PAGE_ID = "microsoft-pc"
API_TITLE = "Microsoft Planetary Computer STAC API"
API_DESCRIPTION = (
    "Searchable spatiotemporal metadata describing Earth science datasets "
    "hosted by the Microsoft Planetary Computer"
)

TILER_HREF_ENV_VAR = "TILER_HREF"

EXTENSIONS = [
    # STAC API Extensions
    QueryExtension(),
    SortExtension(),
    FieldsExtension(),
    FilterExtension(
        conformance_classes=[
            FilterConformanceClasses.FILTER,
            FilterConformanceClasses.ITEM_SEARCH_FILTER,
            FilterConformanceClasses.BASIC_CQL,
            FilterConformanceClasses.CQL_JSON,
        ]
    ),
    # stac_fastapi extensions
    TokenPaginationExtension(),
]


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
