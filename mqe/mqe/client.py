import logging
from typing import List
from urllib.parse import urljoin

import attr
from stac_fastapi.pgstac.core import CoreCrudClient
from stac_fastapi.types.errors import NotFoundError
from stac_fastapi.types.stac import Collection, Collections, Item, ItemCollection

from mqe.cache import collections_endpoint_cache
from mqe.config import API_DESCRIPTION, API_LANDING_PAGE_ID, API_TITLE, get_settings
from mqe.search import MQESearch
from mqe.tiles import TileInfo
from pqecommon.render import COLLECTION_RENDER_CONFIG

settings = get_settings()


logger = logging.getLogger(__name__)


@attr.s
class MQEClient(CoreCrudClient):
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
        render_config = COLLECTION_RENDER_CONFIG.get(collection_id)
        if render_config and render_config.should_add_collection_links:
            TileInfo(collection_id, render_config).inject_collection(collection)

        collection.get("links", []).append(
            {
                "rel": "describedby",
                "href": urljoin(
                    "https://planetarycomputer.microsoft.com/dataset",
                    collection["id"],
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
            render_config = COLLECTION_RENDER_CONFIG.get(collection_id)
            if render_config and render_config.should_add_item_links:
                TileInfo(collection_id, render_config).inject_item(item)

        return item

    async def all_collections(self, **kwargs) -> Collections:
        """Read collections from the database and inject PQE links.
        Called with `GET /collections`.

        In the Planetary Computer, this method has been modified to inject
        links which facilitate users to accessing rendered assets and
        associated metadata.
        Returns:
            Collections.
        """
        try:
            return collections_endpoint_cache["/collections"]
        except KeyError:
            collections = await super().all_collections(**kwargs)
            modified_collections = []
            for col in collections.get("collections", []):
                render_config = COLLECTION_RENDER_CONFIG.get(col.get("id", ""))
                if render_config and render_config.hidden:
                    pass
                else:
                    modified_collections.append(self.inject_collection_links(col))
            collections["collections"] = modified_collections
            collections_endpoint_cache["/collections"] = collections
            return collections

    async def get_collection(self, id: str, **kwargs) -> Collection:
        """Get collection by id and inject PQE links.
        Called with `GET /collections/{collectionId}`.

        In the Planetary Computer, this method has been modified to inject
        links which facilitate users to accessing rendered assets and
        associated metadata.
        Args:
            id: Id of the collection.
        Returns:
            Collection.
        """
        logger.info(
            "Single collection requested",
            extra={
                "custom_dimensions": {
                    "container": id,
                }
            },
        )
        try:
            render_config = COLLECTION_RENDER_CONFIG.get(id)

            # If there's a configuration and it's set to hidden,
            # pretend we never found it.
            if render_config and render_config.hidden:
                raise NotFoundError

            result = await super().get_collection(id, **kwargs)
        except NotFoundError:
            raise NotFoundError(f"No collection with id '{id}' found!")
        return self.inject_collection_links(result)

    async def _search_base(self, search_request: MQESearch, **kwargs) -> ItemCollection:
        """Cross catalog search (POST).
        Called with `POST /search`.
        Args:
            search_request: search request parameters.
        Returns:
            ItemCollection containing items which match the search criteria.
        """
        result = await super()._search_base(search_request, **kwargs)
        return ItemCollection(
            **{
                **result,
                "features": [
                    self.inject_item_links(i) for i in result.get("features", [])
                ],
            }
        )

    # Override to add fix from https://github.com/stac-utils/stac-fastapi/pull/270
    # TODO: Remove once released (stac-fastapi >2.1.1)
    async def get_item(self, item_id: str, collection_id: str, **kwargs) -> Item:
        """Get item by id.

        Called with `GET /collections/{collectionId}/items/{itemId}`.

        Args:
            id: Id of the item.

        Returns:
            Item.
        """
        # If collection does not exist, NotFoundError wil be raised
        await self.get_collection(collection_id, **kwargs)

        req = MQESearch(ids=[item_id], collections=[collection_id], limit=1)
        item_collection = await self._search_base(req, **kwargs)
        if not item_collection["features"]:
            raise NotFoundError(
                f"Item {item_id} in Collection {collection_id} does not exist."
            )

        return Item(**item_collection["features"][0])

    async def landing_page(self, **kwargs):
        landing = await super().landing_page(**kwargs)
        landing["type"] = "Catalog"
        return landing

    @classmethod
    def create(cls, extra_conformance_classes: str = []) -> "MQEClient":
        it = cls(
            landing_page_id=API_LANDING_PAGE_ID,
            title=API_TITLE,
            description=API_DESCRIPTION,
            extra_conformance_classes=extra_conformance_classes,
        )
        return it
