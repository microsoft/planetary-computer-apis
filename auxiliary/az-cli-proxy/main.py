import time
from typing import Any, Optional
from typing import Dict

from azure.core.credentials import AccessToken
from azure.identity import AzureCliCredential
from fastapi import FastAPI

app = FastAPI()


class TokenProvider:
    _instance: Optional["TokenProvider"] = None

    _tokens: Dict[str, Optional[AccessToken]] = {}

    def __init__(self) -> None:
        self._token = None

    def get_token(self, resource: str) -> AccessToken:
        token = self._tokens.get(resource)
        if token is None or token.expires_on < time.time() - 5:
            token = AzureCliCredential().get_token(resource)
            self._tokens[resource] = token
        assert token is not None  # neede for mypy
        return token

    @classmethod
    def get_instance(cls) -> "TokenProvider":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


@app.get("/dev/token")
async def cli_token(resource: str = "") -> Dict[str, Any]:
    """Uses the az cli credential to get a token for the given resource. This is
    meant to mimic the behavior of using managed identities in other spatio
    services in the development environment."""
    accessToken = TokenProvider.get_instance().get_token(resource)
    return {
        "access_token": accessToken.token,
        "expires_on": accessToken.expires_on,
        "resource": resource,
    }
