import json
import os
from urllib.parse import urljoin

import requests

from .test_data import TestData


def ingest_development_data(app_host=None):
    if app_host is None:
        app_host = os.environ.get("STAC_API_HOST")
    if app_host is None:
        raise Exception("STAC_API_HOST env var must be set.")

    collection = None
    with open(TestData.get_path("naip/collection.json")) as f:
        collection = json.load(f)

    items_dir = TestData.get_path("naip/items")
    items = []
    for item_fname in os.listdir(items_dir):
        item_path = os.path.join(items_dir, item_fname)
        with open(item_path) as f:
            items.append(json.load(f))

    existing_collections = requests.get(urljoin(app_host, "/collections")).json()
    if collection["id"] in [c["id"] for c in existing_collections["collections"]]:
        items = []
        all = False
        items_href = urljoin(app_host, f"/collections/{collection['id']}/items")
        while not all:
            r = requests.get(items_href)
            r.raise_for_status()
            item_collection = r.json()
            next_link = next(
                iter(
                    [link for link in item_collection["links"] if link["rel"] == "next"]
                ),
                None,
            )
            if next_link is None:
                all = True
            for i in item_collection["features"]:
                r = requests.delete(
                    urljoin(
                        app_host, f"/collections/{collection['id']}/items/{i['id']}"
                    )
                )

        r = requests.delete(urljoin(app_host, f"/collections/{collection['id']}"))
        r.raise_for_status()

    r = requests.post(urljoin(app_host, "/collections"), json=collection)
    r.raise_for_status()

    for item in items:
        r = requests.post(
            urljoin(app_host, f"/collections/{collection['id']}/items"), json=item
        )
        r.raise_for_status()


if __name__ == "__main__":
    ingest_development_data()
