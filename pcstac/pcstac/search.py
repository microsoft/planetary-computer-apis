import logging
from typing import Any, Dict, List, Optional, Union

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
from pccommon.redis import cached_result
from pcstac.contants import CACHE_KEY_BASE_ITEM
from pydantic import validator
from pydantic.types import conint
from pystac.utils import str_to_datetime
from stac_fastapi.api.models import BaseSearchGetRequest, ItemCollectionUri
from stac_fastapi.pgstac.types.search import PgstacSearch, PgstacSearchContent

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


class PCSearchContent(PgstacSearchContent):
    async def _get_base_item(self, collection_id: str) -> Dict[str, Any]:
        """Return the base item for the collection and cache by collection id."""
        # First check if the instance has a local cache of the base item, then
        # try redis, and finally fetch from the database.
        async def _fetch() -> Dict[str, Any]:
            return await self.client.get_base_item(
                collection_id,
                request=self.request,
            )

        if collection_id not in self.base_items:
            cache_key = f"{CACHE_KEY_BASE_ITEM}:{collection_id}"
            self.base_items[collection_id] = await cached_result(
                _fetch, cache_key, self.request
            )

        return self.base_items[collection_id]


@attr.s
class PCItemCollectionUri(ItemCollectionUri):
    limit: Optional[int] = attr.ib(default=DEFAULT_LIMIT)  # type:ignore


@attr.s
class PCSearchGetRequest(BaseSearchGetRequest):
    limit: Optional[int] = attr.ib(default=DEFAULT_LIMIT)  # type:ignore
