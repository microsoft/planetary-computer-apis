from typing import Any, Dict, Optional

import requests

from stac_fastapi.types.core import AsyncBaseFiltersClient


class MSPCFiltersClient(AsyncBaseFiltersClient):
    """Defines a pattern for implementing the STAC filter extension."""

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
            return await super().get_queryables(collection_id, **kwargs)
        else:
            r = requests.get(
                f"https://planetarycomputer.microsoft.com/stac/{collection_id}/queryables.json"
            )
            return r.json()
