from dataclasses import dataclass
from typing import Any, Dict, Set
from urllib.parse import urljoin

import requests
from cachetools import TTLCache, cached
from fastapi.exceptions import HTTPException

from pqecommon.backoff import with_backoff
from dqe.config import get_settings
from dqe.errors import DQEError

STORAGE_ACCOUNT_PROP = "msft:storage_account"
CONTAINER_PROP = "msft:container"


class CollectionNotFoundError(DQEError):
    def __init__(self, collection_id: str) -> None:
        self.collection_id = collection_id

    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=404,
            detail=f"No collection found with id '{self.collection_id}'",
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
    @cached(cache=TTLCache(maxsize=1, ttl=600))
    def get_collections(cls) -> Dict[str, CollectionInfo]:
        href = urljoin(get_settings().stac_api_url, "collections")
        collections = with_backoff(lambda: requests.get(href).json()["collections"])

        # Only return what we need
        return {
            c["id"]: CollectionInfo.from_collection(c)
            for c in collections
            if STORAGE_ACCOUNT_PROP in c
        }

    @classmethod
    @cached(cache=TTLCache(maxsize=1, ttl=600))
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
        return result

    @classmethod
    def get_collection(cls, collection_id: str) -> CollectionInfo:
        collection = cls.get_collections().get(collection_id)
        if collection is None:
            raise CollectionNotFoundError(collection_id=collection_id)
        return collection
