from typing import Any, Dict


def get_param_str(params: Dict[str, Any]) -> str:
    def transform(v: Any) -> str:
        if isinstance(v, list):
            return ",".join([str(x) for x in v])
        return v

    return "&".join([f"{k}={transform(v)}" for k, v in params.items()])
