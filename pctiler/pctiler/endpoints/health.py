from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/_mgmt/ping")
async def ping() -> dict:
    """Liveliness/readiness probe, matching spec used in stac-fastapi"""
    return {"message": "PONG"}
