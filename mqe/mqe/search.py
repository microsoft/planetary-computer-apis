from typing import Optional

import attr
from pydantic.types import conint
from stac_fastapi.api.models import ItemCollectionUri, SearchGetRequest
from stac_fastapi.pgstac.types.search import PgstacSearch

DEFAULT_LIMIT = 250


class MQESearch(PgstacSearch):
    # Increase the default limit for performance
    # Ignore "Illegal type annotation: call expression not allowed"
    limit: Optional[conint(ge=0, le=10000)] = DEFAULT_LIMIT  # type:ignore


@attr.s
class MQEItemCollectionUri(ItemCollectionUri):
    limit: Optional[int] = attr.ib(default=DEFAULT_LIMIT)  # type:ignore


@attr.s
class MQESearchGetRequest(SearchGetRequest):
    limit: Optional[int] = attr.ib(default=DEFAULT_LIMIT)  # type:ignore
