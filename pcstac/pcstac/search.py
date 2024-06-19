import re
import logging
from typing import Any, Callable, Coroutine, Dict, Optional

import attr
from pydantic import Field, field_validator
from stac_fastapi.api.models import BaseSearchGetRequest, ItemCollectionUri
from stac_fastapi.types.rfc3339 import str_to_interval, DateTimeType
from stac_fastapi.pgstac.types.base_item_cache import BaseItemCache
from stac_fastapi.pgstac.types.search import PgstacSearch
from starlette.requests import Request
from typing_extensions import Annotated

from pccommon.redis import cached_result
from pcstac.contants import CACHE_KEY_BASE_ITEM

DEFAULT_LIMIT = 250

logger = logging.getLogger(__name__)


def _patch_datetime(value: str) -> str:
    values = value.split("/")
    for ix, v in enumerate(values):
        if re.match(r"^(\d\d\d\d)\-(\d\d)\-(\d\d)$", v):
            values[ix] = f"{v}T00:00:00Z"
    return "/".join(values)


class PCSearch(PgstacSearch):
    # Increase the default limit for performance
    # Ignore "Illegal type annotation: call expression not allowed"
    limit: Annotated[Optional[int], Field(strict=True, ge=1, le=1000)] = DEFAULT_LIMIT

    @field_validator("datetime", mode="before")
    @classmethod
    def validate_datetime_before(cls, value: str) -> str:
        """Add HH-MM-SS and Z to YYYY-MM-DD datetime."""
        return _patch_datetime(value)


class RedisBaseItemCache(BaseItemCache):
    """
    Return the base item for the collection and cache by collection id.
    First check if the instance has a local cache of the base item, then
    try redis, and finally fetch from the database.
    """

    def __init__(
        self,
        fetch_base_item: Callable[[str], Coroutine[Any, Any, Dict[str, Any]]],
        request: Request,
    ):
        self._base_items: dict = {}
        super().__init__(fetch_base_item, request)

    async def get(self, collection_id: str) -> Dict[str, Any]:
        async def _fetch() -> Dict[str, Any]:
            return await self._fetch_base_item(collection_id)

        if collection_id not in self._base_items:
            cache_key = f"{CACHE_KEY_BASE_ITEM}:{collection_id}"
            self._base_items[collection_id] = await cached_result(
                _fetch, cache_key, self._request
            )

        return self._base_items[collection_id]


@attr.s
class PCItemCollectionUri(ItemCollectionUri):
    limit: Optional[int] = attr.ib(default=DEFAULT_LIMIT)  # type:ignore


def patch_and_convert(interval: Optional[str]) -> Optional[DateTimeType]:
    """Patch datetime to add hh-mm-ss and timezone info."""
    if interval:
        interval = _patch_datetime(interval)
    return str_to_interval(interval)


@attr.s
class PCSearchGetRequest(BaseSearchGetRequest):
    datetime: Optional[DateTimeType] = attr.ib(
        default=None, converter=patch_and_convert
    )
    limit: Optional[int] = attr.ib(default=DEFAULT_LIMIT)  # type:ignore
