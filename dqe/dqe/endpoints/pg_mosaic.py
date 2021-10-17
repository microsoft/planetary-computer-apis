from typing import Any, Callable, Dict

from fastapi import Depends, Query
from starlette.requests import Request
from titiler.pgstac.factory import MosaicTilerFactory as PgstacMosaicTilerFactory
from titiler.pgstac.models import SearchQuery

from dqe.colormaps import PCColorMapParams
from dqe.config import get_settings
from dqe.db import Connection, with_retry_connection
from dqe.reader import CustomPGSTACBackend


def AdditionalTileParam(
    collection: str = Query(None, description="JSON encoded custom Colormap"),
) -> Dict[str, Any]:
    return {"collection": collection}


class PCDynamicMosaicTilerFactory(PgstacMosaicTilerFactory):

    # Overwrite search routes to have more specific database
    # connection failing logic.
    # TODO: Push back into titiler-pgstac if appropriate.
    def _search_routes(self) -> None:
        """register search routes."""

        @self.router.post(
            "/register",
            responses={200: {"description": "Register a Search."}},
        )
        def register_search(request: Request, body: SearchQuery) -> Dict[str, Any]:
            """Register a Search query."""
            pool = request.app.state.writepool

            def register_search(conn: Connection) -> Dict[str, Any]:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT * FROM search_query(%s);",
                            (body.json(exclude_none=True),),
                        )
                        r = cursor.fetchone()
                        fields = list(map(lambda x: x[0], cursor.description))
                        return dict(zip(fields, r))

            search_info = with_retry_connection(pool, register_search)

            searchid = search_info["hash"]
            return {
                "searchid": searchid,
                "metadata": self.url_for(request, "info_search", searchid=searchid),
                "tiles": self.url_for(request, "tilejson", searchid=searchid),
            }

        @self.router.get(
            "/{searchid}/info",
            responses={200: {"description": "Get Search query metadata."}},
        )
        def info_search(
            request: Request, searchid: Callable = Depends(self.path_dependency)
        ) -> Dict[str, Any]:
            """Get Search query metadata."""
            pool = request.app.state.readpool

            def get_search_info(conn: Connection) -> Dict[str, Any]:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM searches WHERE hash=%s;",
                        (searchid,),
                    )
                    r = cursor.fetchone()
                    fields = list(map(lambda x: x[0], cursor.description))
                    return dict(zip(fields, r))

            return with_retry_connection(pool, get_search_info)


pgstac_mosaic_factory = PCDynamicMosaicTilerFactory(
    reader=CustomPGSTACBackend,  # type:ignore
    router_prefix=get_settings().mosaic_endpoint_prefix,
    colormap_dependency=PCColorMapParams,
    additional_dependency=AdditionalTileParam,
)
