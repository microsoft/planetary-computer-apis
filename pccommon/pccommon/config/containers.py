from typing import Optional

from pydantic import BaseModel

from pccommon.tables import ModelTableService


class ContainerConfig(BaseModel):
    has_cdn: bool = False

    # json_loads/json_dumps config have been removed
    # the authors seems to indicate that parsing/serialization
    # in Rust (pydantic-core) is fast (but maybe not as fast as orjson)
    # https://github.com/pydantic/pydantic/discussions/6388
    # class Config:
    #     json_loads = orjson.loads
    #     json_dumps = orjson_dumps


class ContainerConfigTable(ModelTableService[ContainerConfig]):
    _model = ContainerConfig

    def get_config(
        self, storage_account: str, container: str
    ) -> Optional[ContainerConfig]:
        return self.get(storage_account, container)

    def set_config(
        self, storage_account: str, container: str, config: ContainerConfig
    ) -> None:
        self.upsert(storage_account, container, config)
