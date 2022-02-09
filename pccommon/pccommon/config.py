import logging
from functools import partial
from typing import Optional

from cachetools import Cache, LRUCache, TTLCache, cachedmethod
from cachetools.func import lru_cache
from cachetools.keys import hashkey
from pydantic import BaseModel, BaseSettings, Field

from pccommon.collections import CollectionConfigTable, DefaultRenderConfig
from pccommon.tables import ModelTableService

logger = logging.getLogger(__name__)


ENV_VAR_PCAPIS_PREFIX = "PCAPIS_"
APP_INSIGHTS_INSTRUMENTATION_KEY = "APP_INSIGHTS_INSTRUMENTATION_KEY"


class TableConfig(BaseModel):
    account_name: str
    account_key: str
    table_name: str
    account_url: Optional[str] = None


class ContainerConfig(BaseModel):
    has_cdn: bool = False


class ContainerConfigTable(ModelTableService[ContainerConfig]):
    _model = ContainerConfig
    _cache: Cache = TTLCache(maxsize=1024, ttl=600)

    @cachedmethod(cache=lambda self: self._cache)
    def get_config(
        self, storage_account: str, container: str
    ) -> Optional[ContainerConfig]:
        with self as table:
            return table.get(storage_account, container)

    def set_config(
        self, storage_account: str, container: str, config: ContainerConfig
    ) -> None:
        with self as table:
            table.upsert(storage_account, container, config)


class CommonConfig(BaseSettings):
    _cache: Cache = LRUCache(maxsize=1024)

    app_insights_instrumentation_key: Optional[str] = Field(  # type: ignore
        default=None,
        env=APP_INSIGHTS_INSTRUMENTATION_KEY,
    )
    collection_config: TableConfig
    container_config: TableConfig

    debug: bool = False

    @cachedmethod(cache=lambda self: self._cache, key=partial(hashkey, "collections"))
    def get_collection_config_table(self) -> CollectionConfigTable:
        return CollectionConfigTable.from_account_key(
            account_url=self.collection_config.account_url,
            account_name=self.collection_config.account_name,
            account_key=self.collection_config.account_key,
            table_name=self.collection_config.table_name,
        )

    @cachedmethod(cache=lambda self: self._cache, key=partial(hashkey, "container"))
    def get_container_config_table(self) -> ContainerConfigTable:
        return ContainerConfigTable.from_account_key(
            account_url=self.container_config.account_url,
            account_name=self.container_config.account_name,
            account_key=self.container_config.account_key,
            table_name=self.container_config.table_name,
        )

    @classmethod
    @lru_cache(maxsize=1)
    def from_environment(cls) -> "CommonConfig":
        return CommonConfig()  # type: ignore

    class Config:
        env_prefix = ENV_VAR_PCAPIS_PREFIX
        extra = "ignore"
        env_nested_delimiter = "__"


def get_render_config(collection_id: str) -> Optional[DefaultRenderConfig]:
    table = CommonConfig.from_environment().get_collection_config_table()
    collection_config = table.get_config(collection_id)
    if collection_config:
        return collection_config.render_config
    else:
        return None
