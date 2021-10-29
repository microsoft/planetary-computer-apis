from pydantic import BaseModel


class TileMatrixRef(BaseModel):
    """Tile Matrix references used when constructing /tiles response"""

    tileMatrixSet: str
    tileMatrixSetURI: str


class PCAssetPath(BaseModel):
    collection: str
    item: str
    asset: str
