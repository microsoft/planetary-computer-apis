from urllib.parse import urljoin

import requests

from dqe.config import get_settings
from dqe.models import PCAssetPath

item_path_template = urljoin(
    get_settings().stac_api_url, "collections/{collection_id}/items/{item_id}"
)


def get_asset_url(path: PCAssetPath) -> str:
    """Convert a PCAssetPath to its corresponding metadata item URL"""
    item_path = item_path_template.format(
        collection_id=path.collection, item_id=path.item
    )
    req = requests.get(item_path)
    return req.json()["assets"][path.asset]["href"]
