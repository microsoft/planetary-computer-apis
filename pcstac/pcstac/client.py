import logging
import time
from typing import Any, List, Optional, Type
from urllib.parse import urljoin

import attr
from fastapi import Request
from stac_fastapi.pgstac.core import CoreCrudClient
from stac_fastapi.types.errors import NotFoundError
from stac_fastapi.types.stac import (
    Collection,
    Collections,
    Item,
    ItemCollection,
    LandingPage,
)

from pccommon.config import get_all_render_configs, get_render_config
from pccommon.config.collections import DefaultRenderConfig
from pccommon.constants import DEFAULT_COLLECTION_REGION
from pccommon.logging import get_custom_dimensions
from pccommon.redis import back_pressure, cached_result, rate_limit
from pccommon.tracing import add_stac_attributes_from_search
from pcstac.config import API_DESCRIPTION, API_LANDING_PAGE_ID, API_TITLE, get_settings
from pcstac.contants import (
    CACHE_KEY_COLLECTION,
    CACHE_KEY_COLLECTIONS,
    CACHE_KEY_ITEM,
    CACHE_KEY_ITEMS,
    CACHE_KEY_LANDING_PAGE,
    CACHE_KEY_SEARCH,
)
from pcstac.search import PCSearch
from pcstac.tiles import TileInfo

settings = get_settings()


logger = logging.getLogger(__name__)


@attr.s
class PCClient(CoreCrudClient):
    """Client for core endpoints defined by stac."""

    extra_conformance_classes: List[str] = attr.ib(factory=list)

    def inject_collection_extras(
        self,
        collection: Collection,
        request: Request,
        render_config: Optional[DefaultRenderConfig] = None,
    ) -> Collection:
        """Add extra/non-mandatory links, assets, and properties to a Collection"""

        collection_id = collection.get("id", "")
        config = render_config or get_render_config(collection_id)
        if config:
            tile_info = TileInfo(collection_id, config, request)
            if config.should_add_collection_links:
                tile_info.inject_collection(collection)

            if config.has_vector_tiles:
                tile_info.inject_collection_vectortile_assets(collection)

        if "msft:region" not in collection:
            collection["msft:region"] = DEFAULT_COLLECTION_REGION

        collection.get("links", []).append(
            {
                "rel": "describedby",
                "href": urljoin(
                    "https://planetarycomputer.microsoft.com/dataset/",
                    collection_id,
                ),
                "title": "Human readable dataset overview and reference",
                "type": "text/html",
            }
        )

        return collection

    def inject_item_links(self, item: Item, request: Request) -> Item:
        """Add extra/non-mandatory links to an Item"""
        collection_id = item.get("collection", "")
        if collection_id:
            render_config = get_render_config(collection_id)
            if render_config and render_config.should_add_item_links:
                TileInfo(collection_id, render_config, request).inject_item(item)

        return item

    @rate_limit(CACHE_KEY_COLLECTIONS, settings.rate_limits.collections)
    @back_pressure(
        CACHE_KEY_COLLECTIONS,
        settings.back_pressures.collections.req_per_sec,
        settings.back_pressures.collections.inc_ms,
    )
    async def all_collections(self, request: Request, **kwargs: Any) -> Collections:
        """Read collections from the database and inject PQE links.
        Called with `GET /collections`.

        In the Planetary Computer, this method has been modified to inject
        links which facilitate users to accessing rendered assets and
        associated metadata.
        Returns:
            Collections.
        """
        _super: CoreCrudClient = super()

        async def _fetch() -> Collections:
            collections = await _super.all_collections(request=request, **kwargs)
            render_configs = get_all_render_configs()
            modified_collections = []
            for col in collections.get("collections", []):
                collection_id = col.get("id", "")
                render_config = render_configs.get(
                    collection_id,
                    DefaultRenderConfig(
                        create_links=False, minzoom=0, render_params={}
                    ),
                )
                if render_config and render_config.hidden:
                    pass
                else:
                    modified_collections.append(
                        self.inject_collection_extras(col, request, render_config)
                    )
            collections["collections"] = modified_collections
            return collections

        return await cached_result(_fetch, CACHE_KEY_COLLECTIONS, request)

    @rate_limit(CACHE_KEY_COLLECTION, settings.rate_limits.collection)
    @back_pressure(
        CACHE_KEY_COLLECTION,
        settings.back_pressures.collection.req_per_sec,
        settings.back_pressures.collection.inc_ms,
    )
    async def get_collection(
        self, collection_id: str, request: Request, **kwargs: Any
    ) -> Collection:
        """Get collection by id and inject PQE links.
        Called with `GET /collections/{collection_id}`.

        In the Planetary Computer, this method has been modified to inject
        links which facilitate users to accessing rendered assets and
        associated metadata.
        Args:
            collection_id: Id of the collection.
        Returns:
            Collection.
        """
        _super: CoreCrudClient = super()

        async def _fetch() -> Collection:
            try:
                render_config = get_render_config(collection_id)

                # If there's a configuration and it's set to hidden,
                # pretend we never found it.
                if render_config and render_config.hidden:
                    raise NotFoundError

                result = await _super.get_collection(
                    collection_id, request=request, **kwargs
                )
            except NotFoundError:
                raise NotFoundError(f"No collection with id '{collection_id}' found!")
            return self.inject_collection_extras(result, request, render_config)

        cache_key = f"{CACHE_KEY_COLLECTION}:{collection_id}"
        return await cached_result(_fetch, cache_key, request)

    @rate_limit(CACHE_KEY_SEARCH, settings.rate_limits.search)
    @back_pressure(
        CACHE_KEY_SEARCH,
        settings.back_pressures.search.req_per_sec,
        settings.back_pressures.search.inc_ms,
    )
    async def _search_base(
        self, search_request: PCSearch, request: Request, **kwargs: Any
    ) -> ItemCollection:
        """Cross catalog search (POST).
        Called with `POST /search`.
        Args:
            search_request: search request parameters.
        Returns:
            ItemCollection containing items which match the search criteria.
        """
        _super: CoreCrudClient = super()

        async def _fetch() -> ItemCollection:
            result = await _super._search_base(
                search_request, request=request, **kwargs
            )

            # Remove context extension until we fully support it.
            result.pop("context", None)

            ts = time.perf_counter()
            item_collection = ItemCollection(
                **{
                    **result,
                    "features": [
                        self.inject_item_links(i, request)
                        for i in result.get("features", [])
                    ],
                }
            )
            te = time.perf_counter()
            logger.info(
                "Perf: item search result post processing",
                extra=get_custom_dimensions({"duration": f"{te - ts:0.4f}"}, request),
            )
            return item_collection

        search_json = search_request.model_dump_json()
        add_stac_attributes_from_search(search_json, request)

        logger.info(
            "STAC: Item search body",
            extra=get_custom_dimensions({"search_body": search_json}, request),
        )

        hashed_search = hash(search_json)
        cache_key = f"{CACHE_KEY_SEARCH}:{hashed_search}"
        return await cached_result(_fetch, cache_key, request)

    async def landing_page(self, request: Request, **kwargs: Any) -> LandingPage:
        _super: CoreCrudClient = super()

        async def _fetch() -> LandingPage:
            landing = await _super.landing_page(request=request, **kwargs)
            return landing

        return await cached_result(_fetch, CACHE_KEY_LANDING_PAGE, request)

    @rate_limit(CACHE_KEY_ITEMS, settings.rate_limits.items)
    @back_pressure(
        CACHE_KEY_ITEMS,
        settings.back_pressures.items.req_per_sec,
        settings.back_pressures.items.inc_ms,
    )
    async def item_collection(
        self,
        collection_id: str,
        request: Request,
        limit: Optional[int] = None,
        token: Optional[str] = None,
        **kwargs: Any,
    ) -> ItemCollection:
        _super: CoreCrudClient = super()

        async def _fetch() -> ItemCollection:
            return await _super.item_collection(
                collection_id, request=request, limit=limit, token=token, **kwargs
            )

        cache_key = f"{CACHE_KEY_ITEMS}:{collection_id}:limit:{limit}:token:{token}"
        return await cached_result(_fetch, cache_key, request)

    @rate_limit(CACHE_KEY_ITEM, settings.rate_limits.item)
    @back_pressure(
        CACHE_KEY_ITEM,
        settings.back_pressures.item.req_per_sec,
        settings.back_pressures.item.inc_ms,
    )
    async def get_item(
        self, item_id: str, collection_id: str, request: Request, **kwargs: Any
    ) -> Item:
        _super: CoreCrudClient = super()

        async def _fetch() -> Item:
            item = await _super.get_item(
                item_id, collection_id, request=request, **kwargs
            )
            return item

        cache_key = f"{CACHE_KEY_ITEM}:{collection_id}:{item_id}"
        return await cached_result(_fetch, cache_key, request)

    @classmethod
    def create(
        cls,
        post_request_model: Type[PCSearch],
        extra_conformance_classes: List[str] = [],
    ) -> "PCClient":
        # MyPy is apparently confused by the inheritance here;
        # ignore 'unexpected keyword'
        it = cls(  # type: ignore
            landing_page_id=API_LANDING_PAGE_ID,
            title=API_TITLE,
            description=API_DESCRIPTION,
            extra_conformance_classes=extra_conformance_classes,
            post_request_model=post_request_model,
        )
        return it
