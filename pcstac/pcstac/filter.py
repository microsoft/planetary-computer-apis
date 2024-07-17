from typing import Any, Dict, Optional

from buildpg import render
from fastapi import Request
from stac_fastapi.pgstac.extensions.filter import FiltersClient
from stac_fastapi.types.errors import NotFoundError

from pccommon.redis import cached_result
from pcstac.contants import CACHE_KEY_QUERYABLES


class PCFiltersClient(FiltersClient):
    async def get_queryables(
        self, request: Request, collection_id: Optional[str] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """Override pgstac backend get_queryables to make use of cached results"""

        async def _fetch() -> Dict:
            pool = request.app.state.readpool

            async with pool.acquire() as conn:
                q, p = render(
                    """
                        SELECT * FROM get_queryables(:collection::text);
                    """,
                    collection=collection_id,
                )
                queryables = await conn.fetchval(q, *p)
                if not queryables:
                    raise NotFoundError(f"Collection {collection_id} not found")

                queryables["$id"] = str(request.url)
                return queryables

        cache_key = f"{CACHE_KEY_QUERYABLES}:{collection_id}"
        return await cached_result(_fetch, cache_key, request)
