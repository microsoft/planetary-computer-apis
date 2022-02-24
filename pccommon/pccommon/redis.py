import logging
from typing import Any, Callable, Coroutine, Optional, TypeVar

import orjson
from fastapi import FastAPI, HTTPException, Request
from redis.asyncio import Redis

from pccommon.config.core import PCAPIsConfig
from pccommon.constants import HTTP_429_TOO_MANY_REQUESTS, RATE_LIMIT_KEY_PREFIX
from pccommon.utils import get_request_ip

logger = logging.getLogger(__name__)

T = TypeVar("T")

# From fastapi-limiter
rate_limit_lua_script = """local key = KEYS[1]
local limit = tonumber(ARGV[1])
local expire_time = ARGV[2]
local current = tonumber(redis.call('get', key) or "0")
if current > 0 then
 if current + 1 > limit then
 return redis.call("PTTL",key)
 else
        redis.call("INCR", key)
 return 0
 end
else
    redis.call("SET", key, 1,"px",expire_time)
 return 0
end"""


async def connect_to_redis(app: FastAPI) -> None:
    settings = PCAPIsConfig.from_environment()
    r = Redis(
        host=settings.redis_hostname,
        password=settings.redis_password,
        port=settings.redis_port,
        ssl=settings.redis_ssl,
        decode_responses=True,
    )
    script_hash = await r.script_load(rate_limit_lua_script)

    app.state.redis = r
    app.state.redis_rate_limit_script_hash = script_hash


async def cached_result(
    fn: Callable[[], Coroutine[Any, Any, T]], cache_key: str, request: Request
) -> T:
    settings = PCAPIsConfig.from_environment()
    r: Optional[Redis] = None
    try:
        r = request.app.state.redis
        if r:
            cached: str = await r.get(cache_key)
            if cached:
                return orjson.loads(cached)
    except Exception as e:
        # Don't fail on redis failure
        logger.error(
            f"Error in cache: {e}",
            extra={"custom_dimensions": {"route_key": cache_key}},
        )
        if settings.debug:
            raise

    result = await fn()
    try:
        if r:
            await r.set(cache_key, orjson.dumps(result), settings.redis_ttl)
    except Exception as e:
        # Don't fail on redis failure
        logger.error(
            f"Error in cache: {e}",
            extra={"custom_dimensions": {"route_key": cache_key}},
        )
        if settings.debug:
            raise

    return result


async def rate_limit(request: Request, route_key: str, max_req_per_sec: int) -> None:
    settings = PCAPIsConfig.from_environment()
    try:
        ip = get_request_ip(request)
        r: Redis = request.app.state.redis
        script_hash = request.app.state.redis_rate_limit_script_hash

        key = f"{RATE_LIMIT_KEY_PREFIX}:{route_key}:{ip}"
        pexpire = await r.evalsha(script_hash, 1, key, str(max_req_per_sec), "1000")
        if pexpire > 0:
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Too Many Requests",
                headers={"Retry-After": str(1)},  # 1 second
            )
    except HTTPException:
        raise
    except Exception:
        if settings.debug:
            raise
