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
    """
    A single predefined CQL2-JSON query representing a named mosaic.

    Attributes
    ----------
    name:
        A short name for this mosaic that describes its content, ideally less
        than 30 chars (e.g. "Sept - March, 2021 (low cloud)").
    description:
        A longer description of the mosaic that can be used to explain its content,
        if name is not sufficient.
    cql:
        A valid CQL2-JSON query
    """

    name: str
    description: Optional[str] = None
    cql: List[Dict[str, Any]]


class LegendConfig(CamelModel):
    """
    Defines overrides for dynamic legend generation.

    Attributes
    ----------
    type:
        Legend type to make, one of: `continuous`, `classmap`, `interval` or
        `none` (note, `none` is a string literal).
    labels:
        List of string labels, ideally fewer than 3 items. Will be flex
        spaced-between under the lagend image.
    trim_start:
        The number of items to trim from the start of the legend definition.
        Used if there are values important for rendering (e.g. nodata) that
        aren't desirable in the legend.
    trim_end:
        Same as trim_start, but for the end of the legend definition.
    scale_factor:
        A factor to multiply interval legend labels by. Useful for scaled
        reasters whose colormap definitions map to unscaled values, effectively
        showing legend labels as scaled values.
    """

    type: Optional[str]
    labels: Optional[List[str]]
    trim_start: Optional[int]
    trim_end: Optional[int]
    scale_factor: Optional[float]


class RenderOptions(CamelModel):
    """
    Defines a set of map-tile render options for a collection.

    Attributes
    ----------
    name:
        A short name for this render option that describes its content, ideally
        less than 30 chars (e.g. `True Color`).
    description:
        A longer description of the render option that can be used to explain
        its content.
    options:
        A URL query-string encoded string of TiTiler rendering options. See
        "Query Parameters":
        https://developmentseed.org/titiler/endpoints/cog/#description
    min_zoom:
        Zoom level at which to start rendering the layer.
    legend:
        An optional legend configuration.
    """

    name: str
    description: Optional[str] = None
    options: str
    min_zoom: int
    legend: Optional[LegendConfig] = None


class DefaultLocation(CamelModel):
    """
    Defines a default location for showcasing a collection.

    Attributes
    ----------
    zoom:
        Zoom level at which to center the map.
    coordinates:
        Coordinates at which to center the map, [latitude, longitude]
    """

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
