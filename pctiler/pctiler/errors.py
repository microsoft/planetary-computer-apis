from abc import ABC, abstractmethod

from fastapi import HTTPException


class TilerError(Exception, ABC):
    @abstractmethod
    def to_http(self) -> HTTPException:
        pass


class VectorTileError(TilerError):
    def __init__(
        self,
        collection: str,
        tileset_id: str,
        z: int,
        x: int,
        y: int,
    ) -> None:
        super().__init__(
            f"Error loading tile {z}/{x}/{y} for tileset: '{tileset_id}' in "
            f"collection: '{collection}'"
        )
        self.collection = collection
        self.tileset_id = tileset_id
        self.z = z
        self.x = x
        self.y = y

    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=500,
        )


class VectorTileNotFoundError(VectorTileError):
    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=404,
            detail=(
                f"Tile {self.z}/{self.x}/{self.y} not found for tileset "
                f"{self.tileset_id} in collection {self.collection}"
            ),
        )
