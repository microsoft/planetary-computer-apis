import json
from typing import Any, Callable, Dict, Generic, Optional, Tuple, Type, TypeVar

from azure.core.credentials import AzureNamedKeyCredential, AzureSasCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.data.tables import TableClient, TableServiceClient
from cachetools import Cache, TTLCache, cachedmethod
from pydantic import BaseModel

from pccommon.constants import DEFAULT_TABLE_TTL

T = TypeVar("T", bound="TableService")
M = TypeVar("M", bound=BaseModel)
V = TypeVar("V")


class TableConfig(BaseModel):
    account_url: str
    table_name: str
    sas_token: str


class TableError(Exception):
    pass


def encode_model(m: BaseModel) -> str:
    return m.json()


def decode_dict(s: str) -> Dict[str, Any]:
    return json.loads(s)


class TableService:
    def __init__(
        self,
        get_clients: Callable[[], Tuple[Optional[TableServiceClient], TableClient]],
        ttl: Optional[int] = None,
    ) -> None:
        self._get_clients = get_clients
        self._service_client: Optional[TableServiceClient] = None
        self._table_client: Optional[TableClient] = None
        self._cache: Cache = TTLCache(maxsize=1024, ttl=ttl or DEFAULT_TABLE_TTL)

    def _ensure_table_client(self) -> None:
        if not self._table_client:
            raise TableError("Table client not initialized. Use as a context manager.")

    def __enter__(self) -> TableClient:
        self._service_client, self._table_client = self._get_clients()
        return self._table_client

    def __exit__(self, *args: Any) -> None:
        if self._table_client:
            self._table_client.close()
            self._table_client = None
        if self._service_client:
            self._service_client.close()
            self._service_client = None

    @classmethod
    def from_sas_token(
        cls: Type[T], account_url: str, sas_token: str, table_name: str
    ) -> T:
        def _get_clients(
            _url: str = account_url, _token: str = sas_token, _table: str = table_name
        ) -> Tuple[Optional[TableServiceClient], TableClient]:
            table_service_client = TableServiceClient(
                endpoint=_url,
                credential=AzureSasCredential(_token),
            )
            return (
                table_service_client,
                table_service_client.get_table_client(table_name=_table),
            )

        return cls(_get_clients)

    @classmethod
    def from_connection_string(
        cls: Type[T], connection_string: str, table_name: str
    ) -> T:
        def _get_clients(
            _conn_str: str = connection_string, _table: str = table_name
        ) -> Tuple[Optional[TableServiceClient], TableClient]:
            table_service_client = TableServiceClient.from_connection_string(
                conn_str=_conn_str
            )
            return (
                table_service_client,
                table_service_client.get_table_client(table_name=_table),
            )

        return cls(_get_clients)

    @classmethod
    def from_account_key(
        cls: Type[T],
        account_name: str,
        account_key: str,
        table_name: str,
        account_url: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> T:
        def _get_clients(
            _name: str = account_name,
            _key: str = account_key,
            _url: Optional[str] = account_url,
            _table: str = table_name,
        ) -> Tuple[Optional[TableServiceClient], TableClient]:
            _url = _url or f"https://{_name}.table.core.windows.net"
            credential = AzureNamedKeyCredential(name=_name, key=_key)
            table_service_client = TableServiceClient(
                endpoint=_url, credential=credential
            )
            return (
                table_service_client,
                table_service_client.get_table_client(table_name=_table),
            )

        return cls(_get_clients, ttl=ttl)


class ModelTableService(Generic[M], TableService):
    _model: Type[M]

    def insert(self, partition_key: str, row_key: str, entity: M) -> None:
        with self as table_client:
            table_client.create_entity(
                {
                    "PartitionKey": partition_key,
                    "RowKey": row_key,
                    "Data": encode_model(entity),
                }
            )

    def upsert(self, partition_key: str, row_key: str, entity: M) -> None:
        with self as table_client:
            table_client.upsert_entity(
                {
                    "PartitionKey": partition_key,
                    "RowKey": row_key,
                    "Data": encode_model(entity),
                }
            )

    def update(self, partition_key: str, row_key: str, entity: M) -> None:
        with self as table_client:
            table_client.update_entity(
                {
                    "PartitionKey": partition_key,
                    "RowKey": row_key,
                    "Data": encode_model(entity),
                }
            )

    @cachedmethod(cache=lambda self: self._cache)
    def get(self, partition_key: str, row_key: str) -> Optional[M]:
        with self as table_client:
            try:
                entity = table_client.get_entity(
                    partition_key=partition_key, row_key=row_key
                )
                data: Any = entity.get("Data")
                if not data:
                    raise TableError(
                        "Data column expected but not found. "
                        f"partition_key={partition_key} row_key={row_key}"
                    )
                if not isinstance(data, str):
                    raise TableError(
                        "Data column must be a string. "
                        f"partition_key={partition_key} row_key={row_key}"
                    )
                return self._model(**decode_dict(data))
            except ResourceNotFoundError:
                return None
