from typing import Any, Dict, List, Optional

import orjson
from humps import camelize
from pydantic import BaseModel

from pccommon.tables import ModelTableService
from pccommon.utils import get_param_str, orjson_dumps


class DefaultRenderConfig(BaseModel):
    """
    A class used to represent information convenient for accessing
    the rendered assets of a collection.

    The parameters stored by this class are not the only parameters
    by which rendering is possible or useful but rather represent the
    most convenient renderings for human consumption and preview.
    For example, if a TIF asset can be viewed as an RGB approximating
    normal human vision, parameters will likely encode this rendering.
    """

    render_params: Dict[str, Any]
    minzoom: int
    assets: Optional[List[str]] = None
    maxzoom: Optional[int] = 18
    create_links: bool = True
    has_mosaic: bool = False
    mosaic_preview_zoom: Optional[int] = None
    mosaic_preview_coords: Optional[List[float]] = None
    requires_token: bool = False
    hidden: bool = False  # Hide from API

    def get_full_render_qs(self, collection: str, item: Optional[str] = None) -> str:
        """
        Return the full render query string, including the
        item, collection, render and assets parameters.
        """
        collection_part = f"collection={collection}" if collection else ""
        item_part = f"&item={item}" if item else ""
        asset_part = self.get_assets_params()
        render_part = self.get_render_params()

        return "".join([collection_part, item_part, asset_part, render_part])

    def get_assets_params(self) -> str:
        """
        Convert listed assets to a query string format with multiple `asset` keys
            None -> ""
            [data1] -> "&asset=data1"
            [data1, data2] -> "&asset=data1&asset=data2"
        """
        assets = self.assets or []
        keys = ["&assets="] * len(assets)
        params = ["".join(item) for item in zip(keys, assets)]

        return "".join(params)

    def get_render_params(self) -> str:
        return f"&{get_param_str(self.render_params)}"

    @property
    def should_add_collection_links(self) -> bool:
        # TODO: has_mosaic flag is legacy from now-deprecated
        # sqlite mosaicjson feature. We can reuse this logic
        # for injecting Explorer links for collections. Modify
        # this logic and resulting STAC links to point to
        # the Collection in the Explorer.
        return self.has_mosaic and self.create_links and (not self.hidden)

    @property
    def should_add_item_links(self) -> bool:
        return self.create_links and (not self.hidden)

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class CamelModel(BaseModel):
    class Config:
        alias_generator = camelize
        allow_population_by_field_name = True
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class Mosaics(CamelModel):
    name: str
    description: Optional[str] = None
    cql: List[Dict[str, Any]]


class LegendConfig(CamelModel):
    type: Optional[str]
    labels: Optional[List[str]]
    trim_start: Optional[int]
    trim_end: Optional[int]


class RenderOptions(CamelModel):
    name: str
    description: Optional[str] = None
    options: str
    min_zoom: int
    legend: Optional[LegendConfig] = None


class DefaultLocation(CamelModel):
    zoom: int
    coordinates: List[float]


class MosaicInfo(CamelModel):
    mosaics: List[Mosaics]
    render_options: List[RenderOptions]
    default_location: DefaultLocation
    default_custom_query: Optional[Dict[str, Any]] = None


class CollectionConfig(BaseModel):
    render_config: DefaultRenderConfig
    queryables: Dict[str, Any]
    mosaic_info: MosaicInfo

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class CollectionConfigTable(ModelTableService[CollectionConfig]):
    _model = CollectionConfig

    def get_config(self, collection_id: str) -> Optional[CollectionConfig]:
        return self.get("", collection_id)

    def set_config(self, collection_id: str, config: CollectionConfig) -> None:
        self.upsert("", collection_id, config)
