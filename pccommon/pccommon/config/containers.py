from typing import Callable, Optional, Tuple

from azure.data.tables import TableServiceClient, TableClient
from pydantic import BaseModel

from pccommon.tables import ModelTableService


class ContainerConfig(BaseModel):
    has_cdn: bool = False


class ContainerConfigTable(ModelTableService[ContainerConfig]):
    _model = ContainerConfig

    def __init__(
        self,
        get_clients: Callable[[], Tuple[Optional[TableServiceClient], TableClient]],
    ) -> None:
        super().__init__(get_clients)

    def get_config(
        self, storage_account: str, container: str
    ) -> Optional[ContainerConfig]:
        return self.get(storage_account, container)

    def set_config(
        self, storage_account: str, container: str, config: ContainerConfig
    ) -> None:
        self.upsert(storage_account, container, config)
