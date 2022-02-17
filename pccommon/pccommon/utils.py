import urllib.parse
from typing import Any, Callable, Dict, Optional, TypeVar

import orjson

T = TypeVar("T")
U = TypeVar("U")


def get_param_str(params: Dict[str, Any]) -> str:
    def transform(v: Any) -> str:
        if isinstance(v, list):
            return ",".join([urllib.parse.quote_plus(str(x)) for x in v])
        return urllib.parse.quote_plus(str(v))

    return "&".join([f"{k}={transform(v)}" for k, v in params.items()])


def map_opt(fn: Callable[[T], U], v: Optional[T]) -> Optional[U]:
    """Maps the value of an option to another value, returning
    None if the input option is None.
    """
    return v if v is None else fn(v)


def orjson_dumps(v: Dict[str, Any], *args: Any, default: Any) -> str:
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()
