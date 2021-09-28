import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Set

import requests
from azure.data.tables import TableClient
from cachetools import TTLCache, cached
from fastapi.exceptions import HTTPException

from pqecommon.backoff import with_backoff
from sas.config import ConfigError, SASEndpointConfig
from sas.errors import MESSAGE_500, SASError

logger = logging.getLogger(__name__)

STORAGE_ACCOUNT_PROP = "msft:storage_account"
CONTAINER_PROP = "msft:container"

ADDITIONAL_COLLECTIONS_FILE = "/opt/src/sas/additional_collections.json"
ADDITIONAL_CONTAINERS_FILE = "/opt/src/sas/additional_containers.json"

PC_API_SA_CONN_STR_ENV_VAR = "PC_API_SA_CONN_STRING"
SAS_CONTAINERS_TABLE_ENV_VAR = "PC_API_SA_CONTAINER_TABLE"


class CollectionNotFoundError(SASError):
    def __init__(self, collection_id: str) -> None:
        self.collection_id = collection_id

    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=404,
            detail=f"No collection found with id '{self.collection_id}'",
        )


class CollectionReadError(SASError):
    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=500,
            detail=MESSAGE_500,
        )


@dataclass
class CollectionInfo:
    """Slimmed down version of collection information."""

    # I don't think we need a lot of collection information,
    # and the Pydantic/PySTAC models would probably slow things
    # down. Though at some point we may need to switch to using
    # the full models.

    storage_account: str
    container: str

    @classmethod
    def from_collection(cls, collection: Dict[str, Any]) -> "CollectionInfo":
        return CollectionInfo(
            storage_account=collection[STORAGE_ACCOUNT_PROP],
            container=collection[CONTAINER_PROP],
        )


class Collections:
    """Retrieves collections from the MQE to use to determine
    what the storage account and containers are for Collections,
    and what storage accounts and containers to allow for SAS
    token generation.

    TODO: Make this async
    """

    @classmethod
    @cached(cache=TTLCache(maxsize=1, ttl=600))  # type:ignore
    def get_collections(cls) -> Dict[str, CollectionInfo]:
        settings = SASEndpointConfig.from_environment().api_settings
        href = os.path.join(settings.mqe_url, "collections")
        logger.warning(f"Fetching collections from {href}")
        try:
            collections = with_backoff(lambda: requests.get(href).json()["collections"])
        except Exception as e:
            raise CollectionReadError(f"Could not read collections from {href}") from e

        # Only return what we need
        stac_collections = {
            c["id"]: CollectionInfo.from_collection(c)
            for c in collections
            if STORAGE_ACCOUNT_PROP in c
        }

        # Include additional collections so that
        # we can provide SAS tokens for datasets not
        # yet in the STAC DB.

        if os.path.exists(ADDITIONAL_COLLECTIONS_FILE):
            with open(ADDITIONAL_COLLECTIONS_FILE) as f:
                additional_collections = {
                    k: CollectionInfo(v[STORAGE_ACCOUNT_PROP], v[CONTAINER_PROP])
                    for k, v in json.load(f).items()
                }
        else:
            logger.warning(
                f"No additional collections file found at {ADDITIONAL_COLLECTIONS_FILE}"
            )
            additional_collections = {}

        return {**additional_collections, **stac_collections}

    @classmethod
    @cached(cache=TTLCache(maxsize=1, ttl=600))  # type:ignore
    def get_storage_set(cls) -> Dict[str, Set[str]]:
        """Returns information about what storage accounts and
        containers are available.

        Key is the storage account name, the value is the set of
        containers that are valid for that storage account (base case
        is they are one-to-one)
        """
        result: Dict[str, Set[str]] = {}
        for col in cls.get_collections().values():
            if col.storage_account is not None and col.container is not None:
                if col.storage_account not in result:
                    result[col.storage_account] = set()
                result[col.storage_account].add(col.container)

        # Include additional containers so that
        # we can provide SAS tokens for using
        # the Azure SDK unauthenticated

        if os.path.exists(ADDITIONAL_CONTAINERS_FILE):
            with open(ADDITIONAL_CONTAINERS_FILE) as f:
                for sa, containers in json.load(f).items():
                    if sa not in result:
                        result[sa] = set()
                    for c in containers:
                        result[sa].add(c)
        else:
            logger.warning(
                f"No additional containers file found at {ADDITIONAL_CONTAINERS_FILE}"
            )

        # Also include containers listed in the Azure Storage Table,
        # if provided.
        pcapi_conn_str = os.environ.get(PC_API_SA_CONN_STR_ENV_VAR)
        if pcapi_conn_str:
            sas_containers_table = os.environ.get(SAS_CONTAINERS_TABLE_ENV_VAR)
            if not sas_containers_table:
                raise ConfigError(
                    "PC API Storage Account connect string supplied but no "
                    f"{PC_API_SA_CONN_STR_ENV_VAR} env var set."
                )
            table = TableClient.from_connection_string(
                conn_str=pcapi_conn_str, table_name=sas_containers_table
            )
            for obj in table.list_entities():
                sa, container = obj["storage_account"], obj["container"]
                if sa not in result:
                    result[sa] = set()
                result[sa].add(container)
        else:
            logger.warning(
                "No connection string for container table "
                f"found at {PC_API_SA_CONN_STR_ENV_VAR}"
            )

        return result

    @classmethod
    def get_collection(cls, collection_id: str) -> CollectionInfo:
        collection = cls.get_collections().get(collection_id)
        if collection is None:
            logger.warning(
                "Collection not found",
                extra={
                    "custom_dimensions": {
                        "collection_id": collection_id,
                    }
                },
            )
            raise CollectionNotFoundError(collection_id=collection_id)
        return collection
