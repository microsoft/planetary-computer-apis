from unittest.mock import AsyncMock

import pytest

from pcstac.middleware import ProxyHeaderHostMiddleware

inputs = [
    [
        [
            (b"host", b"badhost"),
            (b"x-forwarded-scheme", b"https"),
            (b"x-forwarded-host", b"example"),
            (b"x-forwarded-port", b"8000"),
        ],
        b"example:8000",
    ],
    [
        [
            (b"host", b"badhost"),
            (b"x-forwarded-scheme", b"https"),
            (b"x-forwarded-host", b"badhost,example.net"),
            (b"x-forwarded-port", b"8000"),
        ],
        b"example.net:8000",
    ],
    [
        [
            (b"host", b"badhost"),
            (b"x-forwarded-scheme", b"https"),
            (b"x-forwarded-host", b"badhost"),
            (b"x-forwarded-host", b"example.net"),
            (b"x-forwarded-port", b"8000"),
        ],
        b"example.net:8000",
    ],
    [
        [
            (b"host", b"badhost"),
            (b"x-forwarded-scheme", b"https"),
            (b"x-forwarded-host", b"badhost"),
            (b"x-forwarded-host", b"alsobad,example.net"),
            (b"x-forwarded-port", b"8000"),
        ],
        b"example.net:8000",
    ],
    [
        [
            (b"host", b"badhost:8080"),
            (b"x-forwarded-scheme", b"https"),
            (b"x-forwarded-host", b"localhost:8080"),
        ],
        b"localhost:8080",
    ],
    [
        [
            (b"host", b"goodhost:8080"),
            (b"x-forwarded-scheme", b"https"),
        ],
        b"goodhost:8080",
    ],
]


@pytest.mark.parametrize("scope_headers,output_host", inputs)
async def test_forwarded_for_middleware(scope_headers, output_host):
    middleware = ProxyHeaderHostMiddleware(app=AsyncMock())

    scope = {
        "type": "http",
        "headers": scope_headers,
    }
    receive = AsyncMock()
    send = AsyncMock()

    await middleware(scope, receive, send)

    assert (b"host", output_host) in scope[
        "headers"
    ], "Expected host to match x-forwarded_* values"

    expected_scheme = [
        value.decode() for key, value in scope_headers if key == b"x-forwarded-scheme"
    ][0]
    assert (
        scope["scheme"] == expected_scheme
    ), "Expected scheme to match x-forwarded-scheme value"

    middleware.app.assert_called_once_with(scope, receive, send)
