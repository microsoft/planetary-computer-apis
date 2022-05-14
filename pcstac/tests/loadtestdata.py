import os
from pathlib import Path

import orjson
from pypgstac.load import Loader, Methods, PgstacDB

DATA_DIR = os.path.join(os.path.dirname(__file__), "data-files")
collection = os.path.join(DATA_DIR, "naip/collection.json")
items = os.path.join(DATA_DIR, "naip/items")


def load_test_data() -> None:
    with PgstacDB() as conn:
        loader = Loader(db=conn)
        with open(collection, "rb") as f:
            c = orjson.loads(f.read())
            loader.load_collections([c], Methods.upsert)
        pathlist = Path(items).glob("*.json")
        for path in pathlist:
            with open(str(path), "rb") as f:
                i = orjson.loads(f.read())
                loader.load_items([i], Methods.upsert)


load_test_data()
