from typing import Any, Dict
import urllib.parse


def get_param_str(params: Dict[str, Any]) -> str:
    def transform(v: Any) -> str:
        if isinstance(v, list):
            return ",".join([urllib.parse.quote_plus(str(x)) for x in v])
        return urllib.parse.quote_plus(str(v))

    return "&".join([f"{k}={transform(v)}" for k, v in params.items()])
