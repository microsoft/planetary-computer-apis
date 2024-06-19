from urllib.parse import quote_plus, urljoin

import pystac
from fastapi import Query, Request, Response
from fastapi.templating import Jinja2Templates
from html_sanitizer.sanitizer import Sanitizer
from starlette.responses import HTMLResponse
from titiler.core.factory import MultiBaseTilerFactory
from titiler.pgstac.dependencies import get_stac_item

from pccommon.config import get_render_config
from pctiler.colormaps import PCColorMapParams
from pctiler.config import get_settings
from pctiler.reader import ItemSTACReader, ReaderParams

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore


def ItemPathParams(
    request: Request,
    collection: str = Query(..., description="STAC Collection ID"),
    item: str = Query(..., description="STAC Item ID"),
) -> pystac.Item:
    """STAC Item dependency."""
    return get_stac_item(request.app.state.dbpool, collection, item)


# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(
    directory=str(resources_files(__package__) / "templates")  # type: ignore
)


pc_tile_factory = MultiBaseTilerFactory(
    reader=ItemSTACReader,
    path_dependency=ItemPathParams,
    colormap_dependency=PCColorMapParams,
    reader_dependency=ReaderParams,
    router_prefix=get_settings().item_endpoint_prefix,
    # We remove the titiler default `/map` viewer
    add_viewer=False,
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

    # Sanitize collection and item to avoid XSS when the values are templated
    # into the rendered html page
    sanitizer = Sanitizer()
    collection_sanitized = quote_plus(sanitizer.sanitize(collection))
    item_sanitized = quote_plus(sanitizer.sanitize(item))

    qs = render_config.get_full_render_qs(collection_sanitized, item_sanitized)
    tilejson_url = pc_tile_factory.url_for(request, "tilejson")
    tilejson_url += f"?{qs}"

    item_url = urljoin(
        get_settings().get_stac_api_href(request),
        f"collections/{collection_sanitized}/items/{item_sanitized}",
    )

    return templates.TemplateResponse(
        request,
        name="item_preview.html",
        context={
            "tileJson": tilejson_url,
            "collectionId": collection_sanitized,
            "itemId": item_sanitized,
            "itemUrl": item_url,
        },
    )
