from typing import Optional

import orjson
from pydantic import BaseModel

from pccommon.tables import ModelTableService
from pccommon.utils import orjson_dumps


class ContainerConfig(BaseModel):
    has_cdn: bool = False

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


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
