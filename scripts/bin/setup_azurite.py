#!/bin/bash
"""
Sets up the Azurite development environment.
Meant to execute in a pctasks development docker container.
"""

import json
from pathlib import Path

from azure.data.tables import TableServiceClient

import pccommon
from pccommon.constants import (
    DEFAULT_CONTAINER_CONFIG_TABLE_NAME,
    DEFAULT_COLLECTION_CONFIG_TABLE_NAME,
)
from pccommon.collections import CollectionConfig, CollectionConfigTable
from pccommon.config import ContainerConfig, ContainerConfigTable

TEST_DATA_DIR = Path(pccommon.__file__).parent.parent / "tests" / "data-files"
COLLECTION_CONFIG_PATH = TEST_DATA_DIR / "collection_config.json"
CONTAINER_CONFIG_PATH = TEST_DATA_DIR / "container_config.json"

AZURITE_CONNECT_STRING = (
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey="
    "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq"
    "/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://azurite:10000/devstoreaccount1;"
    "QueueEndpoint=http://azurite:10001/devstoreaccount1;"
    "TableEndpoint=http://azurite:10002/devstoreaccount1;"
)


def setup_azurite() -> None:
    # Tables

    print("~ Setting up tables...")

    table_service_client = TableServiceClient.from_connection_string(
        AZURITE_CONNECT_STRING
    )
    tables = [t.name for t in table_service_client.list_tables()]
    for table in [
        DEFAULT_CONTAINER_CONFIG_TABLE_NAME,
        DEFAULT_COLLECTION_CONFIG_TABLE_NAME,
    ]:
        if table not in tables:
            print(f"~ ~ Creating table {table}...")
            table_service_client.create_table(table)

    with ContainerConfigTable(
        lambda: (
            None,
            table_service_client.get_table_client(DEFAULT_CONTAINER_CONFIG_TABLE_NAME),
        )
    ) as container_config_table:
        with open(CONTAINER_CONFIG_PATH) as f:
            js = json.load(f)
        for container_path, config_dict in js.items():
            sa, container = container_path.split("/")
            container_config_table.set_config(
                sa, container, ContainerConfig(**config_dict)
            )

    with CollectionConfigTable(
        lambda: (
            None,
            table_service_client.get_table_client(DEFAULT_COLLECTION_CONFIG_TABLE_NAME),
        )
    ) as collection_config_table:
        with open(COLLECTION_CONFIG_PATH) as f:
            js = json.load(f)
        for collection_id, config_dict in js.items():
            config = CollectionConfig(**config_dict)
            collection_config_table.set_config(collection_id, config)

    print("~ Done Azurite setup.")


if __name__ == "__main__":
    setup_azurite()
