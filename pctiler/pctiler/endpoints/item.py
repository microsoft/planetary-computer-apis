import json
from dataclasses import dataclass
from typing import Dict
from urllib.parse import urljoin

from cachetools import LRUCache, cached
from cachetools.keys import hashkey
from fastapi import HTTPException, Query, Request, Response
from fastapi.templating import Jinja2Templates
from psycopg_pool import ConnectionPool
from starlette.responses import HTMLResponse
from titiler.core.factory import MultiBaseTilerFactory

from pccommon.config import get_render_config
from pctiler.colormaps import PCColorMapParams
from pctiler.config import get_settings
from pctiler.reader import ItemSTACReader

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore


# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(
    directory=str(resources_files(__package__) / "templates")
)  # type: ignore


def ItemPathParams(
    request: Request,
    collection: str = Query(..., description="STAC Collection ID"),
    item: str = Query(..., description="STAC Item ID"),
) -> Dict:
    the_item = get_item(request.app.state.dbpool, collection, item)
    return the_item


@cached(  # type: ignore
    LRUCache(maxsize=512),
    key=lambda pool, collection, item: hashkey(collection, item),
)
def get_item(pool: ConnectionPool, collection: str, item: str) -> Dict:
    """Get STAC Item from PGStac."""
    req = dict(
        filter={
            "op": "and",
            "args": [
                {
                    "op": "eq",
                    "args": [{"property": "collection"}, collection],
                },
                {"op": "eq", "args": [{"property": "id"}, item]},
            ],
        },
    )
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM search(%s);",
                (json.dumps(req),),
            )
            resp = cursor.fetchone()
            if resp is not None:
                resp = resp[0]
            else:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Item not found for collection id "
                        f"'{collection}' and item id '{item}'"
                    ),
                )
            features = resp.get("features", [])
            if not len(features):
                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Item not found for collection id "
                        f"'{collection}' and item id '{item}'"
                    ),
                )

            return features[0]


@dataclass
class MapParams:
    collection: str = Query(..., description="STAC Collection ID")
    item: str = Query(..., description="STAC Item ID")


pc_tile_factory = MultiBaseTilerFactory(
    reader=ItemSTACReader,
    path_dependency=ItemPathParams,
    colormap_dependency=PCColorMapParams,
    router_prefix=get_settings().item_endpoint_prefix,
)


@pc_tile_factory.router.get("/map", response_class=HTMLResponse)
def map(
    request: Request,
    collection: str = Query(..., description="STAC Collection ID"),
    item: str = Query(..., description="STAC Item ID"),
) -> Response:
    render_config = get_render_config(collection)
    if render_config is None:
        return Response(
            status_code=404,
            content=f"No item map available for collection {collection}",
        )

    qs = render_config.get_full_render_qs(collection, item)
    tilejson_url = pc_tile_factory.url_for(request, "tilejson")
    tilejson_url += f"?{qs}"

    item_url = urljoin(
        get_settings().stac_api_href,
        f"collections/{collection}/items/{item}",
    )

    return templates.TemplateResponse(
        "item_preview.html",
        context={
            "request": request,
            "tileJson": tilejson_url,
            "collectionId": collection,
            "itemId": item,
            "itemUrl": item_url,
        },
    )
