from typing import Dict, Optional, Union

from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient


def get_container_client(
    container_url: str,
    sas_token: Optional[str] = None,
    account_key: Optional[str] = None,
) -> ContainerClient:
    credential: Optional[Union[str, Dict[str, str], DefaultAzureCredential]] = None
    if account_key:
        # Handle Azurite
        if "devstoreaccount1" in container_url:
            credential = {
                "account_name": "devstoreaccount1",
                "account_key": account_key,
            }
        else:
            credential = account_key
    elif sas_token:
        credential = sas_token
    else:
        credential = DefaultAzureCredential()

    return ContainerClient.from_container_url(container_url, credential=credential)
