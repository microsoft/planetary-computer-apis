from typing import Any, Dict, Optional

from stac_fastapi.api.app import StacApi
from stac_fastapi.api.models import create_request_model
from stac_pydantic import ItemCollection

from pccommon.openapi import fixup_schema
from pcstac.search import PCItemCollectionUri

STAC_API_OPENAPI_TAG = "STAC API v1.0.0-beta.2"


class PCStacApi(StacApi):
    """StacApi factory.

    Factory for creating a STAC-compliant FastAPI application.  After instantation, the
    application is accessible from the `PCStacApi.app` attribute. This class differs
    from stac-fastapi in that it generates OpenAPI output compliant with OpenAPI 3.1.
    Future versions of FastAPI are likely to make this extension unnecessary.

    See related, upstream issue here: https://github.com/tiangolo/fastapi/pull/3038
    """

    def customize_openapi(self) -> Optional[Dict[str, Any]]:
        """Customize openapi schema."""
        schema = super().customize_openapi()
        assert schema is not None
        return fixup_schema(self.app.root_path, schema, tag=STAC_API_OPENAPI_TAG)

    # TODO: Allow overriding base_model for ItemCollectionUri upstream in stac-fastapi
    def register_get_item_collection(self) -> None:
        """Register get item collection endpoint (GET /collection/{collection_id}/items).
        Returns:
            None
        """
        get_pagination_model = self.get_extension(self.pagination_extension).GET
        request_model = create_request_model(
            "ItemCollectionURI",
            base_model=PCItemCollectionUri,
            mixins=[get_pagination_model],
        )
        self.router.add_api_route(
            name="Get ItemCollection",
            path="/collections/{collection_id}/items",
            response_model=ItemCollection
            if self.settings.enable_response_models
            else None,
            response_class=self.response_class,
            response_model_exclude_unset=True,
            response_model_exclude_none=True,
            methods=["GET"],
            endpoint=self._create_endpoint(
                self.client.item_collection, request_model, self.response_class
            ),
        )
