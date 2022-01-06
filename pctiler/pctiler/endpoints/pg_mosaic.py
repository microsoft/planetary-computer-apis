from dataclasses import dataclass

from fastapi import Query
from titiler.core import dependencies
from titiler.pgstac.factory import MosaicTilerFactory

from pctiler.colormaps import PCColorMapParams
from pctiler.config import get_settings
from pctiler.reader import PGSTACBackend


@dataclass
class AssetsBidxExprParams(dependencies.AssetsBidxExprParams):

    collection: str = Query(None, description="STAC Collection ID")


pgstac_mosaic_factory = MosaicTilerFactory(
    reader=PGSTACBackend,
    colormap_dependency=PCColorMapParams,
    layer_dependency=AssetsBidxExprParams,
    router_prefix=get_settings().mosaic_endpoint_prefix,
)
