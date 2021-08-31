import logging

from stac_fastapi.pgstac.core import CoreCrudClient
from stac_fastapi.types.errors import NotFoundError
from stac_fastapi.types.stac import Collection, Collections, Item, ItemCollection

from mqe.config import API_DESCRIPTION, API_LANDING_PAGE_ID, API_TITLE, get_settings
from mqe.search import MQESearch
from mqe.tiles import TileInfo
from pqecommon.render import COLLECTION_RENDER_CONFIG

settings = get_settings()


logger = logging.getLogger(__name__)


class MQEClient(CoreCrudClient):
    def inject_collection_links(self, collection: Collection) -> Collection:
        collection_id = collection.get("id", "")
        render_config = COLLECTION_RENDER_CONFIG.get(collection_id)
        if render_config and render_config.should_add_collection_links:
            TileInfo(collection_id, render_config).inject_collection(collection)

        return collection

    def inject_item_links(self, item: Item) -> Item:
        collection_id = item.get("collection", "")
        if collection_id:
            render_config = COLLECTION_RENDER_CONFIG.get(collection_id)
            if render_config and render_config.should_add_item_links:
                TileInfo(collection_id, render_config).inject_item(item)

        return item

    async def all_collections(self, **kwargs) -> Collections:
        collections = await super().all_collections(**kwargs)
        modified_collections = []
        for col in collections.get("collections", []):
            render_config = COLLECTION_RENDER_CONFIG.get(col.get("id", ""))
            if render_config and render_config.hidden:
                pass
            else:
                modified_collections.append(self.inject_collection_links(col))
        collections["collections"] = modified_collections
        return collections

    async def get_collection(self, id: str, **kwargs) -> Collection:
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
        result = await super()._search_base(search_request, **kwargs)
        return ItemCollection(
            **{
                **result,
                "features": [
                    self.inject_item_links(i) for i in result.get("features", [])
                ],
            }
        )

    async def landing_page(self, **kwargs):
        landing = await super().landing_page(**kwargs)
        landing["type"] = "Catalog"
        return landing

    @classmethod
    def create(cls) -> "MQEClient":
        return cls(
            landing_page_id=API_LANDING_PAGE_ID,
            title=API_TITLE,
            description=API_DESCRIPTION,
        )
