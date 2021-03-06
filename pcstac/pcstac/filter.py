import asyncio
from typing import Any, Dict, List, Optional, Set

from fastapi import HTTPException, Request
from stac_fastapi.types.core import AsyncBaseFiltersClient

from pccommon.config import get_collection_config
from pccommon.redis import cached_result
from pcstac.contants import CACHE_KEY_QUERYABLES


class MSPCFiltersClient(AsyncBaseFiltersClient):
    """Defines a pattern for implementing the STAC filter extension."""

    async def get_queryable_intersection(self, request: Request) -> Dict[str, Any]:
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
            *[self.get_queryables(cid) for cid in collection_ids],
            return_exceptions=True
        )
        all_queryables = [
            queryable
            for queryable in all_queryables
            if not isinstance(queryable, Exception)
        ]
        all_properties: List[dict] = [
            queryable["properties"] for queryable in all_queryables
        ]
        all_property_keys: List[Set[str]] = list(
            map(lambda x: set(x.keys()), all_properties)
        )
        intersecting_props = {}
        if len(all_property_keys) > 0:
            property_name_intersection: List[str] = list(
                set.intersection(*all_property_keys)
            )
            maybe_match: Optional[str] = None
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
        return intersection_schema

    async def get_queryables(
        self, collection_id: Optional[str] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """Get the queryables available for the given collection_id.
        If collection_id is None, returns the intersection of all
        queryables over all collections.
        This base implementation returns a blank queryable schema. This is not allowed
        under OGC CQL but it is allowed by the STAC API Filter Extension
        https://github.com/radiantearth/stac-api-spec/tree/master/fragments/filter#queryables
        """
        queryable_resp: Dict[str, Any]
        if not collection_id:

            async def _fetch_queryables() -> Dict[str, Any]:
                request: Request = kwargs["request"]  # type: ignore
                return await self.get_queryable_intersection(request)

            return await cached_result(
                _fetch_queryables, CACHE_KEY_QUERYABLES, kwargs["request"]
            )
        else:
            collection_config = get_collection_config(collection_id)
            if not collection_config or not collection_config.queryables:
                raise HTTPException(status_code=404)
            queryable_resp = collection_config.queryables
        return queryable_resp
