import io
import os
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import aiohttp
from funclib.errors import InvalidInputError
from funclib.models import RenderOptions
from funclib.tiles import register_search_and_get_tile_url as register_tile_url

from .settings import get_settings


async def get_min_zoom(
    collection_id: str, data_api_url_override: Optional[str] = None
) -> Optional[int]:
    settings = get_settings()
    url = settings.get_mosaic_info_url(collection_id, data_api_url_override)
    async with aiohttp.ClientSession() as session:
        resp = await session.get(url, allow_redirects=False)
        if 300 <= resp.status < 400:
            raise InvalidInputError("Data API redirects are not allowed.")
        if not resp.status == 200:
            return None
        mosaic_info = await resp.json()
        renderOptions = mosaic_info.get("renderOptions")
        if not renderOptions:
            return None
        options = renderOptions[0]
        min_zoom = options.get("minZoom")
        if not min_zoom:
            return None
        return int(min_zoom)


def upload_image(gif: io.BytesIO, collection_name: str) -> str:
    settings = get_settings()
    filename = f"mspc-{collection_name}-{uuid4().hex}.png"
    blob_url = os.path.join(settings.output_storage_url, filename)
    with settings.get_container_client() as container_client:
        gif.seek(0)
        container_client.upload_blob(name=filename, data=gif)

    return blob_url


def get_geom_from_cql(cql: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    def _f(d: Union[Dict[str, Any], List[Any]]) -> List[Optional[Dict[str, Any]]]:
        results: List[Optional[Dict[str, Any]]] = []
        if isinstance(d, list):
            for item in d:
                if isinstance(item, dict) or isinstance(item, list):
                    results.extend(_f(item))
        elif isinstance(d, dict):
            if "op" in d:
                if d["op"] == "s_intersects":
                    if "args" not in d:
                        raise ValueError(
                            "Invalid CQL: Missing args in s_intersects op."
                        )
                    args = d["args"]
                    if not isinstance(args, list):
                        raise ValueError(
                            "Invalid CQL: args in s_intersects op must be a list."
                        )
                    if len(args) != 2:
                        raise ValueError(
                            "Invalid CQL: args in s_intersects op "
                            "must be a list of length 2."
                        )
                    first_arg = args[0]
                    if not isinstance(first_arg, dict):
                        raise ValueError(
                            "Invalid CQL: second arg in s_intersects op "
                            "must be a dict."
                        )
                    if "property" not in first_arg:
                        raise ValueError(
                            "Invalid CQL: First arg to s_intersects op "
                            "must have a property key."
                        )
                    if first_arg["property"] != "geometry":
                        raise ValueError(
                            "Invalid CQL: First arg to s_intersects op "
                            "must have a property key of 'geometry'."
                        )
                    second_arg = args[1]
                    if not isinstance(second_arg, dict):
                        raise ValueError(
                            "Invalid CQL: second arg in s_intersects op "
                            "must be a dict."
                        )
                    results.append(second_arg)
            for k in d:
                if isinstance(d[k], dict) or isinstance(d[k], list):
                    results.extend(_f(d[k]))

        return results

    results = [x for x in _f(cql) if x]
    if len(results) > 1:
        raise ValueError("Invalid CQL: Multiple geometries found.")
    if len(results) == 0:
        return None
    return results[0]


async def register_search_and_get_tile_url(
    cql: Dict[str, Any],
    render_options: RenderOptions,
    data_api_url_override: Optional[str] = None,
) -> str:
    settings = get_settings()
    return await register_tile_url(cql, render_options, settings, data_api_url_override)
