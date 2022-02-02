import asyncio
from typing import Any, Dict, List, Optional, Set

import requests
from fastapi import HTTPException, Request
from stac_fastapi.types.core import AsyncBaseFiltersClient


class MSPCFiltersClient(AsyncBaseFiltersClient):
    """Defines a pattern for implementing the STAC filter extension."""

    queryable_intersection = None
    queryable_url_template = (
        "https://planetarycomputer.microsoft.com/stac/{cid}/queryables.json"
    )

    async def get_queryable_intersection(self, request: Request) -> dict:
        """Generate json schema with intersecting properties of all collections.
        When queryables are requested without specifying a collection (/queryable
        from the root), a json schema encapsulating only the properties shared by all
        collections should be returned. This function gathers all collection
        queryables, calculates the intersection, and caches the results so that the
        work can be saved for future queries.
        """
        pool = request.app.state.readpool

        async with pool.acquire() as conn:
            collections = await conn.fetchval(
                """
                SELECT * FROM all_collections();
                """
            )
        collection_ids = [collection["id"] for collection in collections]
        all_queryables = await asyncio.gather(
            *[self.get_queryables(cid) for cid in collection_ids]
        )
        all_properties: List[dict] = [
            queryable["properties"] for queryable in all_queryables
        ]
        all_property_keys: List[Set[str]] = list(
            map(lambda x: set(x.keys()), all_properties)
        )
        property_name_intersection: List[str] = list(
            set.intersection(*all_property_keys)
        )
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
            "properties": intersecting_props,
        }
        self.queryable_intersection = intersection_schema
        return intersection_schema

    async def get_queryables(
        self, collection_id: Optional[str] = None, **kwargs: Dict[str, Any]
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
                queryable_resp = self.queryable_intersection
            else:
                request = kwargs["request"]
                if isinstance(request, Request):
                    queryable_resp = await self.get_queryable_intersection(request)
        else:
            r = requests.get(self.queryable_url_template.format(cid=collection_id))
            if r.status_code == 404:
                raise HTTPException(status_code=404)
            elif r.status_code == 200:
                queryable_resp = r.json()
        return queryable_resp
