from typing import List, Optional

from cogeo_mosaic.mosaic import MosaicJSON
from pydantic import BaseModel


class TileMatrixRef(BaseModel):
    """Tile Matrix references used when constructing /tiles response"""

    tileMatrixSet: str
    tileMatrixSetURI: str


class SpatialExtent(BaseModel):

    bbox: List[List[float]]


class Extent(BaseModel):

    spatial: Optional[SpatialExtent]


class LinkedAsset(BaseModel):
    """Represents links to assets and templated xyz endpoints"""

    title: Optional[str]
    href: str
    rel: str
    type: str
    templated: bool


class OgcTileInfo(BaseModel):
    """This class encapsulates the OGC API - Tiles' "map tiles description" as
    laid out in https://htmlpreview.github.io/?https://github.com/opengeospatial
                /OGC-API-Tiles/blob/master/core/standard/OAPI_Tiles.html#_web_api"""

    extent: Optional[Extent]
    title: Optional[str]
    description: Optional[str]
    tileMatrixSetLinks: List[TileMatrixRef]
    links: List[LinkedAsset]


class PCAssetPath(BaseModel):
    collection: str
    item: str
    asset: str


class CreatePCMosaicJSON(BaseModel):
    """The minimum data required to generate a mosaic definition
    for assets within the PC"""

    asset_paths: List[PCAssetPath]
    max_threads: int = 20
    minzoom: Optional[int] = None
    maxzoom: Optional[int] = None
    overwrite: bool = False


class MosaicJSONWithID(BaseModel):
    mosaic_id: str
    mosaic_def: MosaicJSON
    mosaic_template: str


class DataSet(BaseModel):
    """Blob storage container details for a given data set"""

    account_name: str
    container_name: str
