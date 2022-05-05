import urllib.parse
from typing import Any, Callable, Dict, Optional, TypeVar

import orjson
from fastapi import Request

from pccommon.constants import (
    X_AZURE_CLIENTIP,
    X_FORWARDED_FOR,
    X_ORIGINAL_FORWARDED_FOR,
)

T = TypeVar("T")
U = TypeVar("U")


def get_param_str(params: Dict[str, Any]) -> str:
    parts = []
    for k, v in params.items():
        if isinstance(v, list):
            for v2 in v:
                parts.append(f"{k}={urllib.parse.quote_plus(str(v2))}")
        else:
            parts.append(f"{k}={urllib.parse.quote_plus(str(v))}")

    return "&".join(parts)


def map_opt(fn: Callable[[T], U], v: Optional[T]) -> Optional[U]:
    """Maps the value of an option to another value, returning
    None if the input option is None.
    """
    return v if v is None else fn(v)


def orjson_dumps(v: Dict[str, Any], *args: Any, default: Any) -> str:
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


def get_request_ip(request: Request) -> str:
    """Gets the IP address of the request."""

    ip_header = (
        request.headers.get(X_AZURE_CLIENTIP)  # set by Front Door
        or request.headers.get(X_ORIGINAL_FORWARDED_FOR)
        or request.headers.get(X_FORWARDED_FOR)
    )

    # If multiple IPs, take the last one
    return ip_header.split(",")[-1] if ip_header else ""
