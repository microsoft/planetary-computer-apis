from typing import Dict, Optional, Union

from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient


def get_container_client(
    container_url: str,
    account_key: Optional[str] = None,
) -> ContainerClient:
    credential: Optional[Union[str, Dict[str, str], DefaultAzureCredential]] = None
    if account_key:
        # Handle Azurite
        if container_url.startswith("http://azurite:"):
            credential = {
                "account_name": "devstoreaccount1",
                "account_key": account_key,
            }
        else:
            raise ValueError(
                "Non-azurite account key provided. "
                "Account keys can only be used with Azurite emulator."
            )
    else:
        credential = DefaultAzureCredential()

    return ContainerClient.from_container_url(container_url, credential=credential)
