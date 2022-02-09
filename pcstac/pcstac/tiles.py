from typing import Any, Dict
from urllib.parse import urljoin

import pystac
from stac_fastapi.types.stac import Collection, Item

from pccommon.collections import DefaultRenderConfig
from pcstac.config import get_settings

TILER_HREF = get_settings().tiler_href


class TileInfo:
    """
    A class which organizes information relating STAC entries
    to endpoints which render associated assets. Used within the
    Planetary Computer to inject links from catalog entries to
    tiling endpoints

    ...

    Attributes
    ----------
    collection_id : str
        The ID of a STAC Collection in the PC
    render_config : DefaultRenderConfig
        Details about the collection: e.g. asset names and convenient
        parameters for rendering those assets
    """

    def __init__(self, collection_id: str, render_config: DefaultRenderConfig) -> None:
        self.collection_id = collection_id
        self.render_config = render_config
        self.tiler_href = get_settings().tiler_href

    def inject_collection(self, collection: Collection) -> None:
        """Inject rendering links to a collection"""
        collection.get("links", []).append(self._get_collection_map_link())

        assets = collection.get("assets", {})
        assets["tilejson"] = self._get_collection_tilejson_asset()
        collection["assets"] = assets  # assets not a required property.

    def inject_item(self, item: Item) -> None:
        """Inject rendering links to an item"""
        item_id = item.get("id", "")
        item.get("links", []).append(self._get_item_map_link(item_id))

        assets = item.get("assets", {})
        assets["tilejson"] = self._get_item_tilejson_asset(item_id)
        assets["rendered_preview"] = self._get_item_preview_asset(item_id)

    def _get_collection_tilejson_asset(self) -> Dict[str, Any]:
        qs = self.render_config.get_full_render_qs(self.collection_id)
        href = urljoin(self.tiler_href, f"collection/tilejson.json?{qs}")

        return {
            "title": "Mosaic TileJSON with default rendering",
            "href": href,
            "type": pystac.MediaType.JSON,
            "roles": ["tiles"],
        }

    def _get_collection_map_link(self) -> Dict[str, Any]:
        href = urljoin(
            self.tiler_href,
            f"collection/map?collection={self.collection_id}",
        )

        return {
            "rel": pystac.RelType.PREVIEW,
            "href": href,
            "title": "Map of collection mosaic",
            "type": "text/html",
        }

    def _get_item_preview_asset(self, item_id: str) -> Dict[str, Any]:
        qs = self.render_config.get_full_render_qs(self.collection_id, item_id)
        href = urljoin(self.tiler_href, f"item/preview.png?{qs}")

        return {
            "title": "Rendered preview",
            "rel": "preview",
            "href": href,
            "roles": ["overview"],
            "type": pystac.MediaType.PNG,
        }

    def _get_item_tilejson_asset(self, item_id: str) -> Dict[str, Any]:
        qs = self.render_config.get_full_render_qs(self.collection_id, item_id)
        href = urljoin(self.tiler_href, f"item/tilejson.json?{qs}")

        return {
            "title": "TileJSON with default rendering",
            "href": href,
            "type": pystac.MediaType.JSON,
            "roles": ["tiles"],
        }

    def _get_item_map_link(self, item_id: str) -> Dict[str, Any]:
        href = urljoin(
            self.tiler_href,
            f"item/map?collection={self.collection_id}&item={item_id}",
        )

        return {
            "rel": pystac.RelType.PREVIEW,
            "href": href,
            "title": "Map of item",
            "type": "text/html",
        }
