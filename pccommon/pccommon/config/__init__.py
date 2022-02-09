from typing import Optional

from pccommon.config.collections import DefaultRenderConfig
from pccommon.config.core import PCAPIsConfig


def get_apis_config() -> PCAPIsConfig:
    return PCAPIsConfig.from_environment()


def get_render_config(collection_id: str) -> Optional[DefaultRenderConfig]:
    table = get_apis_config().get_collection_config_table()
    collection_config = table.get_config(collection_id)
    if collection_config:
        return collection_config.render_config
    else:
        return None
