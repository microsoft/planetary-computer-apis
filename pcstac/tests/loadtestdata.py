import os
import asyncio
from pathlib import Path

import orjson
from pypgstac.load import DB, load_iterator, loadopt, tables

DATA_DIR = os.path.join(os.path.dirname(__file__), "data-files")
collection = os.path.join(DATA_DIR, "naip/collection.json")
items = os.path.join(DATA_DIR, "naip/items")


async def load_test_data() -> None:
    async with DB() as conn:
        with open(collection, "rb") as f:
            c = orjson.loads(f.read())
            await load_iterator([c], tables.collections, conn, loadopt.upsert)
        pathlist = Path(items).glob("*.json")
        for path in pathlist:
            with open(str(path), "rb") as f:
                i = orjson.loads(f.read())
                await load_iterator([i], tables.items, conn, loadopt.upsert)

asyncio.run(load_test_data())
