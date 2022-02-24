import logging
from typing import Optional

from cachetools import Cache, LRUCache, cachedmethod
from cachetools.func import lru_cache
from cachetools.keys import hashkey
from pydantic import BaseModel, BaseSettings, Field, PrivateAttr

from pccommon.config.collections import CollectionConfigTable
from pccommon.config.containers import ContainerConfigTable
from pccommon.constants import DEFAULT_TTL

logger = logging.getLogger(__name__)


ENV_VAR_PCAPIS_PREFIX = "PCAPIS_"
APP_INSIGHTS_INSTRUMENTATION_KEY = "APP_INSIGHTS_INSTRUMENTATION_KEY"


class TableConfig(BaseModel):
    account_name: str
    account_key: str
    table_name: str
    account_url: Optional[str] = None


class PCAPIsConfig(BaseSettings):
    _cache: Cache = PrivateAttr(default_factory=lambda: LRUCache(maxsize=10))

    app_insights_instrumentation_key: Optional[str] = Field(  # type: ignore
        default=None,
        env=APP_INSIGHTS_INSTRUMENTATION_KEY,
    )
    collection_config: TableConfig
    container_config: TableConfig

    table_value_ttl: int = Field(default=DEFAULT_TTL)

    redis_hostname: str
    redis_password: str
    redis_port: int
    redis_ssl: bool = True
    redis_ttl: int = Field(default=DEFAULT_TTL)

    debug: bool = False

    @cachedmethod(cache=lambda self: self._cache, key=lambda _: hashkey("collection"))
    def get_collection_config_table(self) -> CollectionConfigTable:
        return CollectionConfigTable.from_account_key(
            account_url=self.collection_config.account_url,
            account_name=self.collection_config.account_name,
            account_key=self.collection_config.account_key,
            table_name=self.collection_config.table_name,
            ttl=self.table_value_ttl,
        )

    @cachedmethod(cache=lambda self: self._cache, key=lambda _: hashkey("container"))
    def get_container_config_table(self) -> ContainerConfigTable:
        return ContainerConfigTable.from_account_key(
            account_url=self.container_config.account_url,
            account_name=self.container_config.account_name,
            account_key=self.container_config.account_key,
            table_name=self.container_config.table_name,
            ttl=self.table_value_ttl,
        )

    @classmethod
    @lru_cache(maxsize=1)
    def from_environment(cls) -> "PCAPIsConfig":
        return PCAPIsConfig()  # type: ignore

    class Config:
        env_prefix = ENV_VAR_PCAPIS_PREFIX
        extra = "ignore"
        env_nested_delimiter = "__"
