from dataclasses import dataclass, field

from fastapi import Query, Request
from fastapi.responses import ORJSONResponse
from psycopg_pool import ConnectionPool
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


@dataclass(init=False)
class BackendParams(dependencies.DefaultDependency):
    """backend parameters."""

    pool: ConnectionPool = field(init=False)
    request: Request = field(init=False)

    def __init__(self, request: Request):
        """Initialize BackendParams"""
        self.pool = request.app.state.dbpool
        self.request = request


pgstac_mosaic_factory = MosaicTilerFactory(
    reader=PGSTACBackend,
    colormap_dependency=PCColorMapParams,
    layer_dependency=AssetsBidxExprParams,
    reader_dependency=ReaderParams,
    router_prefix=get_settings().mosaic_endpoint_prefix,
    backend_dependency=BackendParams,
    add_map_viewer=False,
    add_statistics=False,
    add_mosaic_list=False,
)


@pgstac_mosaic_factory.router.get(
    "/info", response_model=MosaicInfo, response_class=ORJSONResponse
)
def mosaic_info(
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
        content=collection_config.mosaic_info.model_dump(by_alias=True, exclude_unset=True),
    )
