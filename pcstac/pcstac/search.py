import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union

import attr
from geojson_pydantic.geometries import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)
from pydantic import validator
from pydantic.types import conint
from pystac.utils import str_to_datetime
from stac_fastapi.api.models import BaseSearchGetRequest, ItemCollectionUri
from stac_fastapi.pgstac.types.base_item_cache import BaseItemCache
from stac_fastapi.pgstac.types.search import PgstacSearch
from starlette.requests import Request

from pccommon.redis import cached_result
from pcstac.contants import CACHE_KEY_BASE_ITEM

DEFAULT_LIMIT = 250

logger = logging.getLogger(__name__)


class PCSearch(PgstacSearch):
    # Increase the default limit for performance
    # Ignore "Illegal type annotation: call expression not allowed"
    limit: Optional[conint(ge=1, le=1000)] = DEFAULT_LIMIT  # type:ignore

    # Can be removed when
    # https://github.com/stac-utils/stac-fastapi/issues/187 is closed
    intersects: Optional[
        Union[
            Point,
            MultiPoint,
            LineString,
            MultiLineString,
            Polygon,
            MultiPolygon,
            GeometryCollection,
        ]
    ]

    @validator("datetime")
    def validate_datetime(cls, v: str) -> str:
        """Validate datetime.

        Custom to allow for users to supply dates only.
        """
        if "/" in v:
            values = v.split("/")
        else:
            # Single date is interpreted as end date
            values = ["..", v]

        dates: List[str] = []
        for value in values:
            if value == "..":
                dates.append(value)
                continue

            str_to_datetime(value)
            dates.append(value)

        if ".." not in dates:
            if str_to_datetime(dates[0]) > str_to_datetime(dates[1]):
                raise ValueError(
                    "Invalid datetime range, must match format (begin_date, end_date)"
                )

        return v


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


@attr.s
class PCSearchGetRequest(BaseSearchGetRequest):
    limit: Optional[int] = attr.ib(default=DEFAULT_LIMIT)  # type:ignore
