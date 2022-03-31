from typing import Any, Dict, Optional

from stac_fastapi.api.app import StacApi

from pccommon.openapi import fixup_schema
from pcstac.config import STAC_API_VERSION

STAC_API_OPENAPI_TAG = f"STAC API {STAC_API_VERSION}"


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
