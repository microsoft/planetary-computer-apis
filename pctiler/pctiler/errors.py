from abc import ABC, abstractmethod

from fastapi import HTTPException


class TilerError(Exception, ABC):
    @abstractmethod
    def to_http(self) -> HTTPException:
        pass


class VectorTileError(HTTPException):
    def __init__(
        self,
        collection: str,
        tileset_id: str,
        z: int,
        x: int,
        y: int,
    ) -> None:

        super().__init__(
            status_code=500,
            detail=(
                f"Error loading tile {z}/{x}/{y} for tileset: '{tileset_id}' in "
                f"collection: '{collection}'"
            ),
        )


class VectorTileNotFoundError(HTTPException):
    def __init__(
        self,
        collection: str,
        tileset_id: str,
        z: int,
        x: int,
        y: int,
    ) -> None:

        super().__init__(
            status_code=404,
            detail=(
                f"Tile {z}/{x}/{y} not found for tileset "
                f"{tileset_id} in collection {collection}"
            ),
        )
