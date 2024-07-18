import logging
from typing import Callable

import fastapi
import starlette

logger = logging.getLogger(__name__)


def get_endpoint_function(
    router: fastapi.APIRouter, path: str, method: str
) -> Callable:
    for route in router.routes:
        match, _ = route.matches({"type": "http", "path": path, "method": method})
        if match == starlette.routing.Match.FULL:
            # The abstract BaseRoute doesn't have a `.endpoint` attribute,
            # but all of its subclasses do.
            return route.endpoint  # type: ignore [attr-defined]

    logger.warning(f"Could not find endpoint. method={method} path={path}")
    raise fastapi.HTTPException(detail="Internal system error", status_code=500)
