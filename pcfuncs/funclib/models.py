from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

from pydantic import BaseModel


class RenderOptions(BaseModel):
    """Titiler render options.

    See the "Query Parameters" section of
    https://developmentseed.org/titiler/endpoints/stac/
    """

    collection: str

    pixel_selection: Optional[str] = None
    """Pixel selection method.

    One of: first, highest, lowest, mean, median, stdev
    """

    assets: Optional[Union[str, List[str]]] = None
    """Assets to render."""

    asset_bidx: Optional[Union[str, List[str]]] = None
    """Per asset band indexes (e.g. data|1,2,3, cog|1)"""

    expression: Optional[str] = None
    """Band math expression between assets (e.g. asset1 + asset2 / asset3)"""

    asset_expression: Optional[Union[str, List[str]]] = None
    """Per asset band expression (e.g. data|b1*b2+b3, cog|b1+b3)"""

    nodata: Optional[str] = None
    """Overwrite internal Nodata value"""

    unscale: Optional[bool] = None
    """Apply dataset internal Scale/Offset"""

    resampling: Optional[str] = None
    """rasterio resampling method. Default is nearest"""

    rescale: Optional[Union[str, List[str]]] = None
    """comma (',') delimited Min,Max range. Can set multiple time for multiple bands."""

    color_formula: Optional[str] = None
    """rio-color formula"""

    colormap: Optional[str] = None
    """JSON encoded custom Colormap"""

    colormap_name: Optional[str] = None
    """rio-tiler color map name"""

    return_mask: Optional[bool] = None
    """Add mask to the output data. Default is True"""

    buffer: Optional[float] = None
    """Add buffer on each side of the tile (e.g 0.5 = 257x257, 1.0 = 258x258)"""

    scan_limit: Optional[int] = None
    """Return as soon as we scan N items (defaults to 10000 in PgSTAC)"""

    items_limit: Optional[int] = None
    """Return as soon as we have N items per geometry (defaults to 100 in PgSTAC)"""

    time_limit: Optional[int] = None
    """Return after N seconds to avoid long requests (defaults to 5 in PgSTAC)"""

    exitwhenfull: Optional[bool] = None
    """Return as soon as the geometry is fully covered (defaults to True in PgSTAC)"""

    skipcovered: Optional[bool] = None
    """Skip any items that would show up completely under the previous items.

    Defaults to True in PgSTAC
    """

    @property
    def encoded_query_string(self) -> str:
        options = self.model_dump(
            exclude_defaults=True, exclude_none=True, exclude_unset=True
        )
        encoded_options: List[str] = []
        for key, value in options.items():
            if isinstance(value, list):
                for item in value:
                    encoded_options.append(f"{key}={quote(str(item))}")
            else:
                encoded_options.append(f"{key}={quote(str(value))}")
        encoded_options.append("tile_scale=2")
        return "&".join(encoded_options)

    @classmethod
    def from_query_params(cls, render_params: str) -> "RenderOptions":
        result: Dict[str, Any] = {}
        for p in render_params.split("&"):
            k, v = p.split("=")
            if k in result:
                if not isinstance(result[k], list):
                    result[k] = [result[k]]
                result[k].append(v)
            else:
                result[k] = v

        return RenderOptions(**result)
