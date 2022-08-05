from typing import Any, Dict, Optional

from funclib.models import RenderOptions
from funclib.raster import ExportFormats
from pydantic import BaseModel, validator

from .settings import ImageSettings
from .utils import get_geom_from_cql


class ImageRequest(BaseModel):
    cql: Dict[str, Any]
    """CQL query to render.

    This must include a s_intersects op with a geometry
    """

    render_params: str
    """Titiler render params to use for rendering.

    This must include a collection
    """

    cols: int
    """The desired image width in pixels."""

    rows: int
    """The desired image height in pixels."""

    format: ExportFormats = ExportFormats.PNG
    """The desired image format."""

    mask: bool = False
    """If true, the image will be masked with the input geometry."""

    data_api_url: Optional[str] = None
    """Override for the data API URL. Useful for testing."""

    def get_geometry(self) -> Dict[str, Any]:
        geom = get_geom_from_cql(self.cql)
        assert geom
        return geom

    def get_render_options(self) -> RenderOptions:
        return RenderOptions.from_query_params(self.render_params)

    @validator("cql")
    def _validate_cql(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not get_geom_from_cql(v):
            raise ValueError(
                "Invalid CQL: Must contain a geometry in an s_intersects operation"
            )
        return v

    @validator("render_params")
    def _validate_render_params(cls, v: str) -> str:
        RenderOptions.from_query_params(v)
        return v

    @validator("rows")
    def _validate_rows(cls, v: int, values: Dict[str, Any]) -> int:
        settings = ImageSettings.get()
        cols = int(values["cols"])
        if cols * v > settings.max_pixels:
            raise ValueError(
                f"Too many pixels requested: {cols * v} > {settings.max_pixels}. "
                "Choose a smaller image size via reducing cols or rows."
            )
        return v

    def get_collection(self) -> str:
        render_options = self.get_render_options()
        return render_options.collection


class ImageResponse(BaseModel):
    url: str
