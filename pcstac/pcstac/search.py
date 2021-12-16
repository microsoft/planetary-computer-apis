from typing import Optional

import attr
from pydantic.types import conint
from stac_fastapi.api.models import ItemCollectionUri, BaseSearchGetRequest
from stac_fastapi.pgstac.types.search import PgstacSearch

DEFAULT_LIMIT = 250


class PCSearch(PgstacSearch):
    # Increase the default limit for performance
    # Ignore "Illegal type annotation: call expression not allowed"
    limit: Optional[conint(ge=1, le=1000)] = DEFAULT_LIMIT  # type:ignore


@attr.s
class PCItemCollectionUri(ItemCollectionUri):
    limit: Optional[int] = attr.ib(default=DEFAULT_LIMIT)  # type:ignore


@attr.s
class PCSearchGetRequest(BaseSearchGetRequest):
    limit: Optional[int] = attr.ib(default=DEFAULT_LIMIT)  # type:ignore
