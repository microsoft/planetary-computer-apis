from functools import lru_cache

from pydantic import BaseModel, BaseSettings, Field
from stac_fastapi.extensions.core import (
    FieldsExtension,
    FilterExtension,
    QueryExtension,
    SortExtension,
    TokenPaginationExtension,
)
from stac_fastapi.extensions.core.filter.filter import FilterConformanceClasses

from pccommon.config.core import ENV_VAR_PCAPIS_PREFIX, PCAPIsConfig
from pcstac.filter import MSPCFiltersClient

API_VERSION = "1.2"
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
        client=MSPCFiltersClient(),
        conformance_classes=[
            FilterConformanceClasses.FILTER,
            FilterConformanceClasses.ITEM_SEARCH_FILTER,
            FilterConformanceClasses.BASIC_CQL,
            FilterConformanceClasses.CQL_JSON,
        ],
    ),
    # stac_fastapi extensions
    TokenPaginationExtension(),
]


class RateLimits(BaseModel):
    collections: int = 100
    collection: int = 100
    item: int = 100
    items: int = 50
    search: int = 50


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

    api = PCAPIsConfig.from_environment()

    tiler_href: str = Field(env="TILER_HREF_ENV_VAR", default="")
    openapi_url: str = "/openapi.json"
    debug: bool = False
    api_version: str = f"v{API_VERSION}"
    rate_limits: RateLimits = RateLimits()

    class Config:
        env_prefix = ENV_VAR_PCAPIS_PREFIX
        extra = "ignore"
        env_nested_delimiter = "__"


@lru_cache
def get_settings() -> Settings:
    return Settings()
