import logging
from typing import Any, List, Optional, Type
from urllib.parse import urljoin

import attr
from stac_fastapi.pgstac.core import CoreCrudClient
from stac_fastapi.types.errors import NotFoundError
from stac_fastapi.types.stac import (
    Collection,
    Collections,
    Item,
    ItemCollection,
    LandingPage,
)

from pccommon.config import get_render_config
from pccommon.redis import cached_result, rate_limit
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

    def conformance_classes(self) -> List[str]:
        """Generate conformance classes list."""
        base_conformance_classes = self.base_conformance_classes.copy()

        for extension in self.extensions:
            extension_classes = getattr(extension, "conformance_classes", [])
            base_conformance_classes.extend(extension_classes)

        base_conformance_classes.extend(self.extra_conformance_classes)

        return sorted(list(set(base_conformance_classes)))

    def inject_collection_links(self, collection: Collection) -> Collection:
        """Add extra/non-mandatory links to a Collection"""
        collection_id = collection.get("id", "")
        render_config = get_render_config(collection_id)
        if render_config and render_config.should_add_collection_links:
            TileInfo(collection_id, render_config).inject_collection(collection)

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

    def inject_item_links(self, item: Item) -> Item:
        """Add extra/non-mandatory links to an Item"""
        collection_id = item.get("collection", "")
        if collection_id:
            render_config = get_render_config(collection_id)
            if render_config and render_config.should_add_item_links:
                TileInfo(collection_id, render_config).inject_item(item)

        return item

    async def all_collections(self, **kwargs: Any) -> Collections:
        """Read collections from the database and inject PQE links.
        Called with `GET /collections`.

        In the Planetary Computer, this method has been modified to inject
        links which facilitate users to accessing rendered assets and
        associated metadata.
        Returns:
            Collections.
        """
        await rate_limit(
            kwargs["request"], CACHE_KEY_COLLECTIONS, settings.rate_limits.collections
        )

        _super: CoreCrudClient = super()

        async def _fetch() -> Collections:
            collections = await _super.all_collections(**kwargs)
            modified_collections = []
            for col in collections.get("collections", []):
                collection_id = col.get("id", "")
                render_config = get_render_config(collection_id)
                if render_config and render_config.hidden:
                    pass
                else:
                    modified_collections.append(self.inject_collection_links(col))
            collections["collections"] = modified_collections
            return collections

        return await cached_result(_fetch, CACHE_KEY_COLLECTIONS, kwargs["request"])

    async def get_collection(self, collection_id: str, **kwargs: Any) -> Collection:
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
        await rate_limit(
            kwargs["request"], CACHE_KEY_COLLECTION, settings.rate_limits.collection
        )

        _super: CoreCrudClient = super()

        async def _fetch() -> Collection:
            try:
                render_config = get_render_config(collection_id)

                # If there's a configuration and it's set to hidden,
                # pretend we never found it.
                if render_config and render_config.hidden:
                    raise NotFoundError

                result = await _super.get_collection(collection_id, **kwargs)
            except NotFoundError:
                raise NotFoundError(f"No collection with id '{collection_id}' found!")
            return self.inject_collection_links(result)

        cache_key = f"{CACHE_KEY_COLLECTION}:{collection_id}"
        return await cached_result(_fetch, cache_key, kwargs["request"])

    async def _search_base(
        self, search_request: PCSearch, **kwargs: Any
    ) -> ItemCollection:
        """Cross catalog search (POST).
        Called with `POST /search`.
        Args:
            search_request: search request parameters.
        Returns:
            ItemCollection containing items which match the search criteria.
        """
        await rate_limit(
            kwargs["request"], CACHE_KEY_SEARCH, settings.rate_limits.search
        )

        _super: CoreCrudClient = super()

        async def _fetch() -> ItemCollection:
            result = await _super._search_base(search_request, **kwargs)

            # Remove context extension until we fully support it.
            result.pop("context", None)

            return ItemCollection(
                **{
                    **result,
                    "features": [
                        self.inject_item_links(i) for i in result.get("features", [])
                    ],
                }
            )

        hashed_search = hash(search_request.json())
        cache_key = f"{CACHE_KEY_SEARCH}:{hashed_search}"
        return await cached_result(_fetch, cache_key, kwargs["request"])

    async def landing_page(self, **kwargs: Any) -> LandingPage:
        _super: CoreCrudClient = super()

        async def _fetch() -> LandingPage:
            landing = await _super.landing_page(**kwargs)
            # Remove once
            # https://github.com/stac-utils/stac-fastapi/issues/334 is fixed.
            del landing["stac_extensions"]
            return landing

        return await cached_result(_fetch, CACHE_KEY_LANDING_PAGE, kwargs["request"])

    async def item_collection(
        self,
        collection_id: str,
        limit: Optional[int] = None,
        token: str = None,
        **kwargs: Any,
    ) -> ItemCollection:
        await rate_limit(kwargs["request"], CACHE_KEY_ITEMS, settings.rate_limits.items)

        _super: CoreCrudClient = super()

        async def _fetch() -> ItemCollection:
            return await _super.item_collection(collection_id, limit, token, **kwargs)

        cache_key = f"{CACHE_KEY_ITEMS}:{collection_id}:limit:{limit}:token:{token}"
        return await cached_result(_fetch, cache_key, kwargs["request"])

    async def get_item(self, item_id: str, collection_id: str, **kwargs: Any) -> Item:
        await rate_limit(kwargs["request"], CACHE_KEY_ITEM, settings.rate_limits.items)

        _super: CoreCrudClient = super()

        async def _fetch() -> Item:
            return await _super.get_item(item_id, collection_id, **kwargs)

        cache_key = f"{CACHE_KEY_ITEM}:{collection_id}:{item_id}"
        return await cached_result(_fetch, cache_key, kwargs["request"])

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
