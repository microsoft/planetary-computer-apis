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


def load_test_queryables() -> None:
    with PgstacDB() as db:
        conn = db.connect()

        # Ensure the username user has pgstac on the search_path
        conn.execute("ALTER ROLE username SET search_path TO pgstac, public")

        # Delete any existing naip queryables
        conn.execute("DELETE FROM queryables WHERE 'naip' = any(collection_ids)")

        conn.execute(
            """
            INSERT INTO pgstac.queryables (name, collection_ids, definition)
            VALUES
                ('naip:year', '{"naip"}', '{"title": "Year", "type": "string"}'),
                ('naip:state', '{"naip"}', '{"title": "State", "type": "string"}');
            """
        )


load_test_data()
load_test_queryables()
