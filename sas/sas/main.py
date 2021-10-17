#!/usr/bin/env python3
import os
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from starlette.middleware.cors import CORSMiddleware

from pqecommon.logging import init_logging
from pqecommon.openapi import fixup_schema
from sas.config import SASEndpointConfig
from sas.routes import sign, token

# Initialize logging
init_logging("sas")

# Get the root path if set in the environment
APP_ROOT_PATH = os.environ.get("APP_ROOT_PATH", "")

settings = SASEndpointConfig.from_environment().api_settings

app = FastAPI(
    title=settings.title,
    openapi_url=settings.openapi_url,
    root_path=APP_ROOT_PATH,
)

app.include_router(
    token.sas_token_endpoint_factory.router,
    prefix="/token",
    tags=["Shared Access Signature (SAS) Tokens to use with Azure SDKs"],
)

app.include_router(
    sign.sas_sign_endpoint_factory.router,
    prefix="/sign",
    tags=["Sign an HREF for read access"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# TODO: Redirect to docs
@app.get("/")
async def read_root() -> Dict[str, str]:
    return {"Hello": "Planetary Developer!"}


def custom_openapi() -> Dict[str, Any]:
    if not app.openapi_schema:
        schema = get_openapi(
            title=settings.title,
            version=settings.api_version,
            routes=app.routes,
        )
        app.openapi_schema = fixup_schema(app.root_path, schema)
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore
