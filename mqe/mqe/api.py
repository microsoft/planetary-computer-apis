from typing import Any, Dict, Optional

from stac_fastapi.api.app import StacApi

from pqecommon.openapi import fixup_schema

STAC_API_OPENAPI_TAG = "STAC API v1.0.0-beta.2"


class PCStacApi(StacApi):
    def customize_openapi(self) -> Optional[Dict[str, Any]]:
        """Customize openapi schema."""
        schema = super().customize_openapi()
        assert schema is not None
        return fixup_schema(self.app.root_path, schema, tag=STAC_API_OPENAPI_TAG)
