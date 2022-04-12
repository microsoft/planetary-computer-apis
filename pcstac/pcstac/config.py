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
DB_MIN_CONN = "DB_MIN_CONN_SIZE"
DB_MAX_CONN = "DB_MAX_CONN_SIZE"

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
    collections: int = 500
    collection: int = 500
    item: int = 500
    items: int = 100
    search: int = 100


class BackPressureConfig(BaseModel):
    req_per_sec: int = 50
    inc_ms: int = 10


class BackPressures(BaseSettings):
    collections: BackPressureConfig
    collection: BackPressureConfig
    item: BackPressureConfig
    items: BackPressureConfig
    search: BackPressureConfig


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

    debug: bool = False
    tiler_href: str = Field(env=TILER_HREF_ENV_VAR, default="")
    db_max_conn_size: int = Field(env=DB_MAX_CONN, default=1)
    db_min_conn_size: int = Field(env=DB_MIN_CONN, default=1)
    openapi_url: str = "/openapi.json"
    api_version: str = f"v{API_VERSION}"
    rate_limits: RateLimits
    back_pressures: BackPressures

    class Config:
        env_prefix = ENV_VAR_PCAPIS_PREFIX
        extra = "ignore"
        env_nested_delimiter = "__"


@lru_cache
def get_settings() -> Settings:
    return Settings()
