from typing import Dict, Optional, Union

from azure.identity import ManagedIdentityCredential
from azure.storage.blob import ContainerClient

from pccommon.constants import AZURITE_ACCOUNT_KEY


def get_container_client(
    container_url: str,
) -> ContainerClient:
    credential: Optional[Union[Dict[str, str], ManagedIdentityCredential]] = None
    # Handle Azurite
    if container_url.startswith("http://azurite:"):
        credential = {
            "account_name": "devstoreaccount1",
            "account_key": AZURITE_ACCOUNT_KEY,
        }
    else:
        credential = ManagedIdentityCredential()

    return ContainerClient.from_container_url(container_url, credential=credential)
