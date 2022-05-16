from dataclasses import dataclass

from fastapi import Query, Request
from fastapi.responses import ORJSONResponse
from titiler.core import dependencies
from titiler.pgstac.factory import MosaicTilerFactory

from pccommon.config import get_collection_config
from pccommon.config.collections import MosaicInfo
from pctiler.colormaps import PCColorMapParams
from pctiler.config import get_settings
from pctiler.reader import PGSTACBackend, ReaderParams


@dataclass
class AssetsBidxExprParams(dependencies.AssetsBidxExprParams):

    collection: str = Query(None, description="STAC Collection ID")


pgstac_mosaic_factory = MosaicTilerFactory(
    reader=PGSTACBackend,
    colormap_dependency=PCColorMapParams,
    layer_dependency=AssetsBidxExprParams,
    reader_dependency=ReaderParams,
    router_prefix=get_settings().mosaic_endpoint_prefix,
)


@pgstac_mosaic_factory.router.get(
    "/info", response_model=MosaicInfo, response_class=ORJSONResponse
)
def map(
    request: Request, collection: str = Query(..., description="STAC Collection ID")
) -> ORJSONResponse:
    collection_config = get_collection_config(collection)
    if not collection_config or not collection_config.mosaic_info:
        return ORJSONResponse(
            status_code=404,
            content=f"No mosaic info available for collection {collection}",
        )

    return ORJSONResponse(
        status_code=200,
        content=collection_config.mosaic_info.dict(by_alias=True, exclude_unset=True),
    )
