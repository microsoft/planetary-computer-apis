import threading
from typing import Any

from azure.core.credentials import AccessToken
from azure.identity import DefaultAzureCredential


class PcDefaultAzureCredential:
    """Singleton wrapper around DefaultAzureCredential to share in memory cache
    between requests and threads. Assumption of thread safety for method calls is
    based on:

    https://github.com/Azure/azure-sdk-for-python/issues/28665
    """

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_token(cls, *scopes: str, **kwargs: Any) -> AccessToken:
        return cls.get_credential().get_token(*scopes, **kwargs)

    @classmethod
    def get_credential(cls) -> DefaultAzureCredential:
        if cls._instance is None:
            with cls._lock:
                cls._instance = DefaultAzureCredential()
        return cls._instance
