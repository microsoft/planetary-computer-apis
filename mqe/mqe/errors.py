from abc import ABC, abstractmethod
from typing import Any, Dict

from asyncpg.exceptions import InvalidPasswordError
from fastapi import HTTPException
from starlette import status

MESSAGE_500 = (
    "Service encountered an error. Please contact planetarycomputer@microsoft.com"
)

MQE_DEFAULT_STATUS_CODES = {InvalidPasswordError: status.HTTP_500_INTERNAL_SERVER_ERROR}


def generic_500() -> HTTPException:
    return HTTPException(status_code=500, detail=MESSAGE_500)


class MQEError(Exception, ABC):
    @abstractmethod
    def to_http(self) -> HTTPException:
        pass


class DuplicateRowError(MQEError):
    def __init__(
        self, collection_id: str, item_id: str, *args: Any, **kwargs: Dict[str, Any]
    ) -> None:
        super().__init__(
            f"Duplicate row found for collection {collection_id}, item {item_id}",
            *args,
            **kwargs,
        )
        self.collection_id = collection_id
        self.item_id = item_id

    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=500,
            detail=MESSAGE_500,
        )
