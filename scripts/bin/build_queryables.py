#!/usr/bin/env python

import json
import os

import requests

STAC_API_ROOT = "https://planetarycomputer.microsoft.com/api/stac/v1"

QUERYABLES_URL_TEMPLATE = "https://planetarycomputer-staging.microsoft.com/api/stac/v1/collections/{collection}/queryables"

QUERYABLE_TEMPLATE = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://example.org/queryables",
    "type": "object",
    "title": "",
    "properties": {
        "id": {
            "title": "Item ID",
            "description": "Item identifier",
            "$ref": "https://schemas.stacspec.org/v1.0.0/item-spec/json-schema/item.json#/definitions/core/allOf/2/properties/id",
        },
        "collection": {
            "title": "Collection ID",
            "description": "The ID of the STAC Collection this Item references to.",
            "$ref": "https://schemas.stacspec.org/v1.0.0/item-spec/json-schema/item.json#/definitions/core/allOf/2/properties/collection",
        },
        "geometry": {
            "title": "Item geometry",
            "description": "The footprint geometry for this Item.",
            "$ref": "https://geojson.org/schema/Geometry.json",
        },
        "datetime": {
            "description": "Datetime",
            "type": "string",
            "title": "Acquired",
            "format": "date-time",
            "pattern": "(\\+00:00|Z)$",
        },
    },
}


def get_current_queryables(collection):
    """Get already existing queryables if available"""
    try:
        return requests.get(
            QUERYABLES_URL_TEMPLATE.format(collection=collection)
        ).json()
    except json.decoder.JSONDecodeError:
        return None


def collection_list():
    """Collect a list of collection IDs"""
    resp = requests.get(STAC_API_ROOT + "/collections")
    data = resp.json()
    collection_ids = [d["id"] for d in data["collections"]]
    return collection_ids


def example_properties(collection_id: str):
    """Get an item to use as an example of collection properties"""
    resp = requests.get(STAC_API_ROOT + f"/search?collections={collection_id}&limit=1")
    data = resp.json()
    try:
        properties = data["features"][0]["properties"]
    except IndexError:
        properties = {}
    return properties


def construct_schema(collection: str, example_properties: dict):
    """Construct a schema for provided properties, using the queryable template"""
    template = get_current_queryables(collection) or QUERYABLE_TEMPLATE.copy()
    for key, value in example_properties.items():
        # pass over fields that are already included or are known to be useless in querying
        if (
            key in ["datetime", "description", "title"]
            or key in template["properties"].keys()
        ):
            continue
        elif isinstance(value, str):
            schema_type = "string"
        elif isinstance(value, (int, float)):
            schema_type = "number"
        elif isinstance(value, list):
            schema_type = "array"
        elif isinstance(value, dict):
            schema_type = "object"
        elif isinstance(value, bool):
            schema_type = "boolean"
        else:
            continue

        template["properties"][key] = {"title": key, "type": schema_type}

    return template


if not (os.path.exists("/opt/src/queryable_schemas")):
    os.mkdir("/opt/src/queryable_schemas")
for collection in collection_list():
    print(f"Constructing schema for {collection}")
    example_props = example_properties(collection)
    schema = construct_schema(collection, example_props)

    with open(f"/opt/src/queryable_schemas/{collection}_schema.json", "w") as f:
        json.dump(schema, f, indent=4, sort_keys=True)
