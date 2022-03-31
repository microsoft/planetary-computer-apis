from typing import List, Optional, Union

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
from stac_fastapi.pgstac.types.search import PgstacSearch

DEFAULT_LIMIT = 250


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


@attr.s
class PCItemCollectionUri(ItemCollectionUri):
    limit: Optional[int] = attr.ib(default=DEFAULT_LIMIT)  # type:ignore


@attr.s
class PCSearchGetRequest(BaseSearchGetRequest):
    limit: Optional[int] = attr.ib(default=DEFAULT_LIMIT)  # type:ignore
