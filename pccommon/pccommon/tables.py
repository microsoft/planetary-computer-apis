import os
from threading import Lock
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import orjson
from azure.core.credentials import AzureNamedKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.data.tables import TableClient, TableEntity, TableServiceClient
from azure.identity import AzureCliCredential, ManagedIdentityCredential
from cachetools import Cache, TTLCache, cachedmethod
from cachetools.keys import hashkey
from pydantic import BaseModel

from pccommon.constants import (
    AZURITE_ACCOUNT_KEY,
    DEFAULT_IP_EXCEPTIONS_TTL,
    DEFAULT_TTL,
    IP_EXCEPTION_PARTITION_KEY,
)

T = TypeVar("T", bound="TableService")
M = TypeVar("M", bound=BaseModel)
V = TypeVar("V", int, str, bool, float)


class TableConfig(BaseModel):
    account_url: str
    table_name: str
    sas_token: str


class TableError(Exception):
    pass


def encode_model(m: BaseModel) -> str:
    return m.json()


def decode_dict(s: str) -> Dict[str, Any]:
    return orjson.loads(s)


class TableService:
    def __init__(
        self,
        get_clients: Callable[[], Tuple[Optional[TableServiceClient], TableClient]],
        ttl: Optional[int] = None,
    ) -> None:
        self._get_clients = get_clients
        self._service_client: Optional[TableServiceClient] = None
        self._table_client: Optional[TableClient] = None
        self._cache: Cache = TTLCache(maxsize=1024, ttl=ttl or DEFAULT_TTL)
        self._cache_lock: Lock = Lock()

    def _get_cache(self) -> Cache:
        return self._cache

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
    def from_environment(
        cls: Type[T],
        account_name: str,
        table_name: str,
        account_url: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> T:
        def _get_clients(
            _account: str = account_name,
            _table: str = table_name,
            _url: Optional[str] = account_url,
        ) -> Tuple[Optional[TableServiceClient], TableClient]:
            credential: Union[
                AzureNamedKeyCredential, ManagedIdentityCredential, AzureCliCredential
            ]

            # Check if the environment is configured to use Azurite and use that key.
            # Otherwise, we must use a workload identity.
            if _url:
                if not _url.startswith("http://azurite:"):
                    raise ValueError(
                        "Non-azurite account url provided. "
                        "Account keys can only be used with Azurite emulator."
                    )

                url = _url
                credential = AzureNamedKeyCredential(
                    name=_account, key=AZURITE_ACCOUNT_KEY
                )
            else:
                client_id = os.environ.get("AZURE_CLIENT_ID")
                credential = (
                    ManagedIdentityCredential(client_id=client_id)
                    if client_id
                    else AzureCliCredential()
                )

                url = f"https://{_account}.table.core.windows.net"

            table_service_client = TableServiceClient(
                endpoint=url, credential=credential
            )

            return (
                table_service_client,
                table_service_client.get_table_client(table_name=_table),
            )

        return cls(_get_clients, ttl=ttl)


class ModelTableService(Generic[M], TableService):
    _model: Type[M]

    def _parse_model(
        self, entity: Dict[str, Any], partition_key: str, row_key: str
    ) -> M:
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

    @cachedmethod(
        cache=lambda self: self._get_cache(),
        lock=lambda self: self._cache_lock,
        key=lambda _, partition_key, row_key: f"get_{partition_key}_{row_key}",
    )
    def get(self, partition_key: str, row_key: str) -> Optional[M]:
        with self as table_client:
            try:
                entity = table_client.get_entity(
                    partition_key=partition_key, row_key=row_key
                )
                return self._parse_model(entity, partition_key, row_key)

            except ResourceNotFoundError:
                return None

    @cachedmethod(
        cache=lambda self: self._get_cache(),
        lock=lambda self: self._cache_lock,
        key=lambda _: "getall",
    )
    def get_all(self) -> Iterable[Tuple[Optional[str], Optional[str], M]]:
        with self as table_client:
            for entity in table_client.query_entities("PartitionKey eq ''"):
                partition_key, row_key = entity.get("PartitionKey"), entity.get(
                    "RowKey"
                )
                yield (
                    partition_key,
                    row_key,
                    self._parse_model(entity, partition_key, row_key),  # type: ignore
                )


class ValueTableService(Generic[V], TableService):
    _type: Type[V]

    def _parse_value(self, entity: TableEntity) -> V:
        partition_key = entity.get("PartitionKey")
        row_key = entity.get("RowKey")
        value = entity.get("Value")
        if value is None:
            raise TableError(
                "Value column expected but not found. "
                f"partition_key={partition_key} row_key={row_key}"
            )

        return self._type(value)

    def insert(self, partition_key: str, row_key: str, value: V) -> None:
        self._ensure_table_client()
        assert self._table_client
        self._table_client.create_entity(
            {
                "PartitionKey": partition_key,
                "RowKey": row_key,
                "Value": value,
            }
        )

    def upsert(self, partition_key: str, row_key: str, value: V) -> None:
        self._ensure_table_client()
        assert self._table_client
        self._table_client.upsert_entity(
            {
                "PartitionKey": partition_key,
                "RowKey": row_key,
                "Value": value,
            }
        )

    def update(self, partition_key: str, row_key: str, value: V) -> None:
        self._ensure_table_client()
        assert self._table_client
        self._table_client.update_entity(
            {
                "PartitionKey": partition_key,
                "RowKey": row_key,
                "Value": value,
            }
        )

    def get(self, partition_key: str, row_key: str) -> Optional[V]:
        self._ensure_table_client()
        assert self._table_client
        try:
            entity = self._table_client.get_entity(
                partition_key=partition_key, row_key=row_key
            )

            return self._parse_value(entity)
        except ResourceNotFoundError:
            return None

    def get_all_values(self) -> Iterable[V]:
        self._ensure_table_client()
        assert self._table_client
        for entity in self._table_client.list_entities():
            yield self._parse_value(entity)


class IPExceptionListTable(ValueTableService[str]):
    _type = str
    _cache: Cache

    def __init__(
        self,
        get_clients: Callable[[], Tuple[Optional[TableServiceClient], TableClient]],
        ttl: Optional[int] = None,
    ) -> None:
        self._cache = TTLCache(maxsize=10, ttl=ttl or DEFAULT_IP_EXCEPTIONS_TTL)
        super().__init__(get_clients, ttl)

    def add_exception(self, ip: str) -> None:
        with self:
            self.upsert(partition_key=IP_EXCEPTION_PARTITION_KEY, row_key=ip, value=ip)

    @cachedmethod(lambda self: self._cache, key=lambda _: hashkey("ip_exceptions"))
    def get_exceptions(self) -> Set[str]:
        """Returns a set of IP addresses that are not subject to rate limiting."""
        with self:
            return set(self.get_all_values())
