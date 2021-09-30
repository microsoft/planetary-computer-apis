from abc import ABC, abstractmethod

from fastapi import HTTPException

MESSAGE_500 = "Service unavailable. Please contact planetarycomputer@microsoft.com"
BAD_LOCATION_MESSAGE = "The given location does not exist or cannot be read"


class SASError(Exception, ABC):
    @abstractmethod
    def to_http(self) -> HTTPException:
        pass


class SASTokenCreationError(SASError):
    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=500,
            detail=MESSAGE_500,
        )


class StorageAccountNotAuthorizedError(SASError):
    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=403,
            detail=BAD_LOCATION_MESSAGE,
        )


class InvalidStorageLocationError(SASError):
    def __init__(self, storage_account: str, container: str) -> None:
        self.storage_account = storage_account
        self.container = container

    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=404,
            detail=BAD_LOCATION_MESSAGE,
        )


class HREFParseError(SASError):
    def __init__(self, href: str) -> None:
        self.href = href

    def to_http(self) -> HTTPException:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse href '{self.href}'",
        )


class NoServicePrincipleError(SASError):
    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=500,
            detail=MESSAGE_500,
        )


class UserDelegationKeyError(SASError):
    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=500,
            detail=MESSAGE_500,
        )


class NoForwardedForHeaderError(SASError):
    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=403,
            detail="Could not determine the original of the request.",
        )


class InvalidIPError(SASError):
    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=403,
            detail="Could not determine the original of the request.",
        )


def generic_500() -> HTTPException:
    return HTTPException(status_code=500, detail=MESSAGE_500)
