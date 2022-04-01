import asyncio
import logging
import threading
from typing import Any, Callable, Coroutine, Optional, TypeVar

import orjson
from fastapi import FastAPI, HTTPException, Request
from redis.asyncio import Redis
from redis.exceptions import NoScriptError
from starlette.datastructures import State

from pccommon.config.core import PCAPIsConfig
from pccommon.constants import (
    BACKPRESSURE_KEY_PREFIX,
    HTTP_429_TOO_MANY_REQUESTS,
    RATE_LIMIT_KEY_PREFIX,
)
from pccommon.utils import get_request_ip

logger = logging.getLogger(__name__)

redis_script_lock = threading.Lock()

T = TypeVar("T")

# From fastapi-limiter
rate_limit_lua_script = """
local key = KEYS[1]
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
    redis.call("SET", key, 1, "px", expire_time)
    return 0
end
"""

back_pressure_lua_script = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local expire_time = ARGV[2]
local current = tonumber(redis.call('get', key) or "0")
if current > 0 then
    redis.call("INCR", key)
    if current + 1 > limit then
        return (current - limit) + 1
    else
        return 0
    end
else
    redis.call("SET", key, 1,"px", expire_time)
    return 0
end
"""


async def connect_to_redis(app: FastAPI) -> None:
    """Connect to redis and store instance and script hashes in app state."""
    settings = PCAPIsConfig.from_environment()
    r = Redis(
        host=settings.redis_hostname,
        password=settings.redis_password,
        port=settings.redis_port,
        ssl=settings.redis_ssl,
        decode_responses=True,
    )
    rate_limit_script_hash = await r.script_load(rate_limit_lua_script)
    back_pressure_script_hash = await r.script_load(back_pressure_lua_script)

    app.state.redis = r
    app.state.redis_rate_limit_script_hash = rate_limit_script_hash
    app.state.redis_back_pressure_script_hash = back_pressure_script_hash


async def reregister_scripts(request: Request) -> None:
    """Attempt to reregister lua scripts if raised as missing."""

    # Avoid multiple threads trying to reregister scripts at once
    with redis_script_lock:
        state: State = request.app.state
        r: Redis = state.redis

        scripts = [
            (state.redis_rate_limit_script_hash, rate_limit_lua_script),
            (state.redis_back_pressure_script_hash, back_pressure_lua_script),
        ]

        exists = await r.script_exists(*[s[0] for s in scripts])
        for script_exists, idx in enumerate(exists):
            if not script_exists:
                await r.script_load(scripts[idx][1])


async def cached_result(
    fn: Callable[[], Coroutine[Any, Any, T]], cache_key: str, request: Request
) -> T:
    """Either get the result from redis or run the function and cache the result."""
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


async def apply_rate_limit(
    request: Request, route_key: str, max_req_per_sec: int
) -> None:
    """
    Apply a rate limit.

    Attributes
    ----------
    request:
        The request to rate limit. The IP address from the request is
        used in the cache key.
    route_key:
        The key representing the route to rate limit, used in the cache key.
    max_req_per_sec:
        The maximum requests per second. If this rate is exceeded,
        a 429 Too Many Requests error is raised.
    """
    settings = PCAPIsConfig.from_environment()
    try:
        ip = get_request_ip(request)
        r: Redis = request.app.state.redis

        # Check if this ip excluded from rate limiting
        if ip in settings.get_ip_exception_list_table().get_exceptions():
            return

        script_hash = request.app.state.redis_rate_limit_script_hash

        key = f"{RATE_LIMIT_KEY_PREFIX}:{route_key}:{ip}"
        pexpire = await r.evalsha(script_hash, 1, key, str(max_req_per_sec), "1000")
        if pexpire > 0:
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Too Many Requests",
                headers={"Retry-After": str(1)},  # 1 second
            )
    except NoScriptError:
        logger.error(
            "Rate limit script not registered in redis, re-registering",
        )
        await reregister_scripts(request)
    except HTTPException:
        raise
    except Exception:
        if settings.debug:
            raise


def rate_limit(
    route_key: str, max_req_per_sec: int
) -> Callable[
    [Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]
]:
    """
    Decorator that applies a rate limit to a function.

    apply_rate_limit will be called before the function is executed.

    Attributes
    ----------
    route_key:
        The key representing the route to rate limit, used in the cache key.
    max_req_per_sec:
        The maximum requests per second. If this rate is exceeded,
        a 429 Too Many Requests error is raised.
    """

    def _decorator(
        fn: Callable[..., Coroutine[Any, Any, T]]
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        async def _wrapper(*args: Any, **kwargs: Any) -> T:
            request: Optional[Request] = kwargs.get("request")
            if request:
                await apply_rate_limit(request, route_key, max_req_per_sec)
            else:
                raise ValueError(f"Missing request in {fn.__name__}")
            return await fn(*args, **kwargs)

        return _wrapper

    return _decorator


async def apply_back_pressure(
    request: Request, route_key: str, req_per_sec: int, inc_ms: int
) -> None:
    """
    Apply back pressure.

    Once the rate limit exceeds req_per_sec, slow down responses
    by sleeping inc_ms milliseconds for each request over the limit.

    Attributes
    ----------
    request:
        The request to apply back pressure to. The IP address from the request is
        used in the cache key.
    route_key:
        The key representing the route to rate limit, used in the cache key.
    req_per_sec:
        After this amount of requests are detected over a second the back pressure
        wil be applied.
    inc_ms:
        The amount of milliseconds to sleep for each request over req_per_sec.
    """
    settings = PCAPIsConfig.from_environment()
    try:
        ip = get_request_ip(request)
        r: Redis = request.app.state.redis

        # Check if this ip excluded from rate limiting
        if ip in settings.get_ip_exception_list_table().get_exceptions():
            return

        script_hash = request.app.state.redis_back_pressure_script_hash

        key = f"{BACKPRESSURE_KEY_PREFIX}:{route_key}:{ip}"
        overage: int = await r.evalsha(script_hash, 1, key, str(req_per_sec), "1000")
        print(f"overage: {overage}")
        if overage > 0:
            await asyncio.sleep((overage * inc_ms) / 1000)

    except NoScriptError:
        logger.error(
            "Back pressure script not registered in redis, re-registering",
        )
        await reregister_scripts(request)
    except HTTPException:
        raise
    except Exception:
        if settings.debug:
            raise


def back_pressure(
    route_key: str, req_per_sec: int, inc_ms: int
) -> Callable[
    [Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]
]:
    """
    Decorator that applies back pressure to a function.

    Attributes
    ----------
    route_key:
        The key representing the route to rate limit, used in the cache key.
    req_per_sec:
        After this amount of requests are detected over a second the back pressure
        wil be applied.
    inc_ms:
        The amount of milliseconds to sleep for each request over req_per_sec.
    """

    def _decorator(
        fn: Callable[..., Coroutine[Any, Any, T]]
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        async def _wrapper(*args: Any, **kwargs: Any) -> T:
            request: Optional[Request] = kwargs.get("request")
            if request:
                await apply_back_pressure(request, route_key, req_per_sec, inc_ms)
            else:
                raise ValueError(f"Missing request in {fn.__name__}")
            return await fn(*args, **kwargs)

        return _wrapper

    return _decorator
