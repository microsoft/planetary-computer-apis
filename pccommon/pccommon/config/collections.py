from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from humps import camelize
from pydantic import BaseModel, Field

from pccommon.tables import ModelTableService
from pccommon.utils import get_param_str


class RenderOptionType(str, Enum):
    def __str__(self) -> str:
        return self.value

    raster_tile = "raster-tile"
    vt_polygon = "vt-polygon"
    vt_line = "vt-line"


class CamelModel(BaseModel):

    model_config = {
        # TODO, see if we can use pydantic native function
        # https://docs.pydantic.dev/latest/api/config/#pydantic.alias_generators.to_camel
        "alias_generator": camelize,
        "populate_by_name": True,
    }


class VectorTileset(CamelModel):
    """
    Defines a static vector tileset for a collection. Used primarily to generate
    tilejson metadata for the collection-level vector tile assets.


    id:
        The id of the vector tileset. This should match the prefix of the blob
        path where the associated vector tiles are stored. Will also be used in
        a URL.
    """

    id: str
    name: Optional[str] = None
    maxzoom: Optional[int] = Field(13, ge=0, le=24)
    minzoom: Optional[int] = Field(0, ge=0, le=24)
    center: Optional[List[float]] = None
    bounds: Optional[List[float]] = None


class DefaultRenderConfig(BaseModel):
    """
    A class used to represent information convenient for accessing
    the rendered assets of a collection.

    The parameters stored by this class are not the only parameters
    by which rendering is possible or useful but rather represent the
    most convenient renderings for human consumption and preview.
    For example, if a TIF asset can be viewed as an RGB approximating
    normal human vision, parameters will likely encode this rendering.

    vector_tilesets:
        TileJSON metadata defining static vector tilesets generated for this
        collection. These are used to generate VT routes included as
        collection-level assets in the STAC metadata as well as resolve paths to
        the VT storage account and container to proxy actual pbf files.
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
    max_items_per_tile: Optional[int] = None
    vector_tilesets: Optional[List[VectorTileset]] = None
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
        default_params = f"&{get_param_str(self.render_params)}"

        if "format" in self.render_params:
            return default_params

        # Enforce PNG rendering when otherwise unspecified
        return default_params + "&format=png"

    def get_vector_tileset(self, tileset_id: str) -> Optional[VectorTileset]:
        """
        Get a tileset by id.
        """
        tilesets = self.vector_tilesets or []
        matches = [tileset for tileset in tilesets if tileset.id == tileset_id]

        return matches[0] if matches else None

    @property
    def has_vector_tiles(self) -> bool:
        return bool(self.vector_tilesets)

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
        spaced-between under the legend image.
    trim_start:
        The number of items to trim from the start of the legend definition.
        Used if there are values important for rendering (e.g. nodata) that
        aren't desirable in the legend.
    trim_end:
        Same as trim_start, but for the end of the legend definition.
    scale_factor:
        A factor to multiply interval legend labels by. Useful for scaled
        rasters whose colormap definitions map to unscaled values, effectively
        showing legend labels as scaled values.
    """

    type: Optional[str] = None
    labels: Optional[List[str]] = None
    trim_start: Optional[int] = None
    trim_end: Optional[int] = None
    scale_factor: Optional[float] = None


class VectorTileOptions(CamelModel):
    """
    Defines a set of vector tile render options for a collection.

    Attributes
    ----------
    tilejson_key:
        The key in the collection-level assets which contains the tilejson URL.
    source_layer:
        The source layer name to render from the associated vector tiles.
    fill_color:
        The fill color for polygons.
    stroke_color:
        The stroke color for lines.
    stroke_width:
        The stroke width for lines.
    filter:
        MapBox Filter Expression to filter vector features by.
    """

    tilejson_key: str
    source_layer: str
    fill_color: Optional[str] = None
    stroke_color: Optional[str] = None
    stroke_width: Optional[int] = None
    filter: Optional[List[Any]] = None


class RenderOptionCondition(CamelModel):
    """
    Defines a property/value condition for a render config to be enabled

    Attributes
    ----------
    property:
        The property to check.
    value:
        The value to check against.
    """

    property: str
    value: Any


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
    type:
        The type of render option, defaults to raster-tile.
    options:
        A URL query-string encoded string of TiTiler rendering options. Valid
        only for `raster-tile` types.  See "Query Parameters":
        https://developmentseed.org/titiler/endpoints/cog/#description
    vector_options:
        Options for rendering vector tiles. Valid only for `vt-polygon` and
        `vt-line` types.
    min_zoom:
        Zoom level at which to start rendering the layer.
    legend:
        An optional legend configuration.
    conditions:
        A list of property/value conditions that must be in the active mosaic
        CQL for this render option to be enabled
    """

    name: str
    description: Optional[str] = None
    type: Optional[RenderOptionType] = Field(default=RenderOptionType.raster_tile)
    options: Optional[str]
    vector_options: Optional[VectorTileOptions] = None
    min_zoom: int
    legend: Optional[LegendConfig] = None
    conditions: Optional[List[RenderOptionCondition]] = None


class AnimationHint(CamelModel):
    """
    Defines hints for animation frame settings, to be used as default overrides, for a
    particular collection. If not set, a global default will be used on the frontend.

    Attributes
    ----------
    unit:
        One of mins, hours, days, weeks, months, years
    step:
        The number of units to increment per frame
    duration:
        The number of seconds to display each frame
    frame_count:
        The total number of frames to generate
    """

    unit: Optional[str] = None
    step: Optional[int] = None
    duration: Optional[int] = None
    frame_count: Optional[int] = None


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
    animation_hint: Optional[AnimationHint] = None


class CollectionConfig(BaseModel):
    render_config: DefaultRenderConfig
    mosaic_info: MosaicInfo


class CollectionConfigTable(ModelTableService[CollectionConfig]):
    _model = CollectionConfig

    def get_config(self, collection_id: str) -> Optional[CollectionConfig]:
        return self.get("", collection_id)

    def set_config(self, collection_id: str, config: CollectionConfig) -> None:
        self.upsert("", collection_id, config)

    def get_all_configs(self) -> List[Tuple[Optional[str], CollectionConfig]]:
        return [(config[1], config[2]) for config in self.get_all()]
