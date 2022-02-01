import asyncio
from functools import reduce
from typing import Any, Dict, Optional

import requests
from fastapi import Request
from fastapi import HTTPException
from stac_fastapi.types.core import AsyncBaseFiltersClient


class MSPCFiltersClient(AsyncBaseFiltersClient):
    """Defines a pattern for implementing the STAC filter extension."""

    queryable_intersection = None

    async def get_queryable_intersection(self, **kwargs) -> Dict[str, Any]:
        request: Request = kwargs["request"]
        pool = request.app.state.readpool

        async with pool.acquire() as conn:
            collections = await conn.fetchval(
                """
                SELECT * FROM all_collections();
                """
            )
        collection_ids = [collection["id"] for collection in collections]
        all_queryables = await asyncio.gather(*[self.get_queryables(cid) for cid in collection_ids])
        all_properties = [queryable["properties"] for queryable in all_queryables]
        property_name_intersection = list(reduce(lambda x, y: x & y.keys(), all_properties))
        intersecting_props = {}
        for name in property_name_intersection:
            for idx, properties in enumerate(all_properties):
                if idx == 0:
                    maybe_match = properties[name]
                else:
                    if properties[name] != maybe_match:
                        break
            if maybe_match is not None:
                intersecting_props[name] = maybe_match

        intersection_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "https://example.org/queryables",
            "type": "object",
            "title": "",
            "properties": intersecting_props
        }
        self.queryable_intersection = intersection_schema
        return intersection_schema

    async def get_queryables(
        self, collection_id: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Get the queryables available for the given collection_id.
        If collection_id is None, returns the intersection of all
        queryables over all collections.
        This base implementation returns a blank queryable schema. This is not allowed
        under OGC CQL but it is allowed by the STAC API Filter Extension
        https://github.com/radiantearth/stac-api-spec/tree/master/fragments/filter#queryables
        """
        if not collection_id:
            if self.queryable_intersection:
                return self.queryable_intersection
            else:
                return await self.get_queryable_intersection(**kwargs)
        else:
            r = requests.get(
                f"https://planetarycomputer.microsoft.com/stac/{collection_id}/queryables.json"
            )
            if r.status_code == 404:
                raise HTTPException(status_code=404)
            elif r.status_code == 200:
                return r.json()
