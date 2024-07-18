from dataclasses import dataclass, field
from typing import Annotated, List, Literal, Optional

from fastapi import APIRouter, Depends, FastAPI, Query, Request, Response
from fastapi.responses import ORJSONResponse
from psycopg_pool import ConnectionPool
from pydantic import Field
from titiler.core import dependencies
from titiler.core.dependencies import ColorFormulaParams
from titiler.core.factory import img_endpoint_params
from titiler.core.resources.enums import ImageType
from titiler.pgstac.dependencies import SearchIdParams, TmsTileParams
from titiler.pgstac.factory import MosaicTilerFactory

from pccommon.config import get_collection_config
from pccommon.config.collections import MosaicInfo
from pctiler.colormaps import PCColorMapParams
from pctiler.config import get_settings
from pctiler.endpoints.dependencies import get_endpoint_function
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
    path_dependency=SearchIdParams,
    colormap_dependency=PCColorMapParams,
    layer_dependency=AssetsBidxExprParams,
    reader_dependency=ReaderParams,
    router_prefix=get_settings().mosaic_endpoint_prefix + "/{search_id}",
    backend_dependency=BackendParams,
    add_statistics=False,
)


def add_collection_mosaic_info_route(
    app: FastAPI,
    *,
    prefix: str = "",
    tags: Optional[List[str]] = None,
) -> None:
    """add `/info` endpoint."""

    @app.get(
        f"{prefix}/info",
        response_model=MosaicInfo,
        response_class=ORJSONResponse,
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
            content=collection_config.mosaic_info.model_dump(
                by_alias=True, exclude_unset=True
            ),
        )


legacy_mosaic_router = APIRouter()


@legacy_mosaic_router.get("/tiles/{search_id}/{z}/{x}/{y}", **img_endpoint_params)
@legacy_mosaic_router.get(
    "/tiles/{search_id}/{z}/{x}/{y}.{format}", **img_endpoint_params
)
@legacy_mosaic_router.get(
    "/tiles/{search_id}/{z}/{x}/{y}@{scale}x", **img_endpoint_params
)
@legacy_mosaic_router.get(
    "/tiles/{search_id}/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params
)
@legacy_mosaic_router.get(
    "/tiles/{search_id}/{tileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params
)
@legacy_mosaic_router.get(
    "/tiles/{search_id}/{tileMatrixSetId}/{z}/{x}/{y}.{format}",
    **img_endpoint_params,
)
@legacy_mosaic_router.get(
    "/tiles/{search_id}/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x",
    **img_endpoint_params,
)
@legacy_mosaic_router.get(
    "/tiles/{search_id}/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
    **img_endpoint_params,
)
def tile_routes(  # type: ignore
    request: Request,
    search_id=Depends(pgstac_mosaic_factory.path_dependency),
    tile=Depends(TmsTileParams),
    tileMatrixSetId: Annotated[  # type: ignore
        Literal[tuple(pgstac_mosaic_factory.supported_tms.list())],
        f"Identifier selecting one of the TileMatrixSetId supported (default: '{pgstac_mosaic_factory.default_tms}')",  # noqa: E501,F722
    ] = pgstac_mosaic_factory.default_tms,
    scale: Annotated[  # type: ignore
        Optional[Annotated[int, Field(gt=0, le=4)]],
        "Tile size scale. 1=256x256, 2=512x512...",  # noqa: E501,F722
    ] = None,
    format: Annotated[
        Optional[ImageType],
        "Default will be automatically defined if the output image needs a mask (png) or not (jpeg).",  # noqa: E501,F722
    ] = None,
    layer_params=Depends(pgstac_mosaic_factory.layer_dependency),
    dataset_params=Depends(pgstac_mosaic_factory.dataset_dependency),
    pixel_selection=Depends(pgstac_mosaic_factory.pixel_selection_dependency),
    tile_params=Depends(pgstac_mosaic_factory.tile_dependency),
    post_process=Depends(pgstac_mosaic_factory.process_dependency),
    rescale=Depends(pgstac_mosaic_factory.rescale_dependency),
    color_formula=Depends(ColorFormulaParams),
    colormap=Depends(pgstac_mosaic_factory.colormap_dependency),
    render_params=Depends(pgstac_mosaic_factory.render_dependency),
    pgstac_params=Depends(pgstac_mosaic_factory.pgstac_dependency),
    backend_params=Depends(pgstac_mosaic_factory.backend_dependency),
    reader_params=Depends(pgstac_mosaic_factory.reader_dependency),
    env=Depends(pgstac_mosaic_factory.environment_dependency),
) -> Response:
    """Create map tile."""
    endpoint = get_endpoint_function(
        pgstac_mosaic_factory.router,
        path="/tiles/{z}/{x}/{y}",
        method=request.method,
    )
    result = endpoint(
        search_id=search_id,
        tile=tile,
        tileMatrixSetId=tileMatrixSetId,
        scale=scale,
        format=format,
        tile_params=tile_params,
        layer_params=layer_params,
        dataset_params=dataset_params,
        pixel_selection=pixel_selection,
        post_process=post_process,
        rescale=rescale,
        color_formula=color_formula,
        colormap=colormap,
        render_params=render_params,
        pgstac_params=pgstac_params,
        backend_params=backend_params,
        reader_params=reader_params,
        env=env,
    )
    return result
