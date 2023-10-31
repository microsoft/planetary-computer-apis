from typing import Any, Dict, List, Optional

from funclib.models import RenderOptions
from pydantic import BaseModel, validator


def _get_render_options(render_params: str) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for p in render_params.split("&"):
        k, v = p.split("=")
        if k not in result:
            result[k] = []
        result[k].append(v)
    return result


class StatisticsRequest(BaseModel):
    bbox: List[float]
    zoom: int
    cql: Dict[str, Any]
    render_params: str

    data_api_url: Optional[str] = None
    """Override for the data API URL. Useful for testing."""

    @validator("render_params")
    def _validate_render_params(cls, v: str) -> str:
        RenderOptions.from_query_params(v)
        return v

    def get_render_options(self) -> RenderOptions:
        return RenderOptions.from_query_params(self.render_params)

    def get_collection(self) -> str:
        render_options = _get_render_options(self.render_params)
        return render_options["collection"][0]
