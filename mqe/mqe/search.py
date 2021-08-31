from typing import Optional

from pydantic.types import conint
from stac_fastapi.pgstac.types.search import PgstacSearch


class MQESearch(PgstacSearch):
    # Increase the default limit for performance
    # Ignore "Illegal type annotation: call expression not allowed"
    limit: Optional[conint(ge=0, le=10000)] = 500  # type:ignore
