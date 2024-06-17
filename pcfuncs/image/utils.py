import io
import os
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlsplit
from uuid import uuid4

import aiohttp
from funclib.models import RenderOptions

from .settings import get_settings


async def get_min_zoom(
    collection_id: str, data_api_url_override: Optional[str] = None
) -> Optional[int]:
    settings = get_settings()
    async with aiohttp.ClientSession() as session:
        resp = await session.get(
            settings.get_mosaic_info_url(collection_id, data_api_url_override)
        )
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
    register_url = settings.get_register_url(data_api_url_override)

    async with aiohttp.ClientSession() as session:
        # Register the search and get the tilejson_url back
        resp = await session.post(register_url, json=cql)
        mosaic_info = await resp.json()
        tilejson_href = [
            link["href"] for link in mosaic_info["links"] if link["rel"] == "tilejson"
        ][0]
        tile_url = f"{tilejson_href}?{render_options.encoded_query_string}"

        # Get the full tile path template
        resp = await session.get(tile_url)
        tilejson = await resp.json()
        tile_url = tilejson["tiles"][0]

        scheme, netloc, path, _, _ = urlsplit(tile_url)
        return f"{scheme}://{netloc}{path}".replace("@1x", "@2x")
