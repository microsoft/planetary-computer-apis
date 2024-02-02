from typing import Dict, Optional

from pccommon.config.collections import CollectionConfig, DefaultRenderConfig
from pccommon.config.core import PCAPIsConfig
from pccommon.utils import map_opt


def get_apis_config() -> PCAPIsConfig:
    return PCAPIsConfig.from_environment()


def get_collection_config(collection_id: str) -> Optional[CollectionConfig]:
    table = get_apis_config().get_collection_config_table()
    return table.get_config(collection_id)


def get_render_config(collection_id: str) -> Optional[DefaultRenderConfig]:
    return map_opt(lambda c: c.render_config, get_collection_config(collection_id))


def get_all_render_configs() -> Dict[str, DefaultRenderConfig]:
    return {
        id: coll.render_config
        for id, coll in get_apis_config()
        .get_collection_config_table()
        .get_all_configs()
        if id is not None
    }
