from typing import Any, Dict, Optional

from funclib.models import RenderOptions
from funclib.raster import ExportFormats
from pydantic import BaseModel, Field, field_validator, ValidationInfo

from .settings import get_settings
from .utils import get_geom_from_cql


class ImageRequest(BaseModel):
    cql: Dict[str, Any]
    """CQL query to render.

    If this does not include a s_intersects op with a geometry,
    a geometry must be supplied.
    """

    geometry: Optional[Dict[str, Any]] = None
    """Geometry of are to capture.

    Must be supplied if cql does not include a s_intersects op with a geometry.
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

    show_branding: bool = Field(default=True, alias="showBranding")
    """Stamp the Microsoft logo on the image"""

    mask: bool = False
    """If true, the image will be masked with the input geometry."""

    data_api_url: Optional[str] = None
    """Override for the data API URL. Useful for testing."""

    def get_geometry(self) -> Dict[str, Any]:
        assert self.geometry
        return self.geometry

    def get_render_options(self) -> RenderOptions:
        return RenderOptions.from_query_params(self.render_params)

    @field_validator("geometry")
    def _validate_cql(
        cls,
        v: Optional[Dict[str, Any]],
        info: ValidationInfo,
    ) -> Dict[str, Any]:
        if not v:
            cql = info.data["cql"]
            v = get_geom_from_cql(cql)
            if not v:
                raise ValueError(
                    "Missing Geometry: Request must contain a geometry "
                    "or the cql contain a geometry in an s_intersects operation"
                )
        return v

    @field_validator("render_params")
    def _validate_render_params(cls, v: str) -> str:
        RenderOptions.from_query_params(v)
        return v

    @field_validator("rows")
    def _validate_rows(cls, v: int, info: ValidationInfo) -> int:
        settings = get_settings()
        cols = int(info.data["cols"])
        if cols * v > settings.max_pixels:
            raise ValueError(
                f"Too many pixels requested: {cols * v} > {settings.max_pixels}. "
                "Choose a smaller image size via reducing cols or rows."
            )
        return v

    @field_validator("show_branding")
    def _validate_show_branding(cls, v: bool, info: ValidationInfo) -> bool:
        if v:
            if info.data["format"] != ExportFormats.PNG:
                raise ValueError("Branding is only supported for PNG images.")
        return v

    def get_collection(self) -> str:
        render_options = self.get_render_options()
        return render_options.collection


class ImageResponse(BaseModel):
    url: str
