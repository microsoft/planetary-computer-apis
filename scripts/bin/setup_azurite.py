#!/bin/bash
"""
Sets up the Azurite development environment.
Meant to execute in a pctasks development docker container.
"""

import json
from pathlib import Path

from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient

import pccommon
from pccommon.config.collections import CollectionConfig, CollectionConfigTable
from pccommon.config.containers import ContainerConfig, ContainerConfigTable
from pccommon.constants import (
    DEFAULT_COLLECTION_CONFIG_TABLE_NAME,
    DEFAULT_CONTAINER_CONFIG_TABLE_NAME,
    DEFAULT_IP_EXCEPTION_CONFIG_TABLE_NAME,
)
from pccommon.tables import IPExceptionListTable

TEST_DATA_DIR = Path(pccommon.__file__).parent.parent / "tests" / "data-files"
COLLECTION_CONFIG_PATH = TEST_DATA_DIR / "collection_config.json"
CONTAINER_CONFIG_PATH = TEST_DATA_DIR / "container_config.json"
ADDITIONAL_CONFIG_PATH = TEST_DATA_DIR / "additional-config"

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
        DEFAULT_IP_EXCEPTION_CONFIG_TABLE_NAME,
    ]:
        if table not in tables:
            print(f"~ ~ Creating table {table}...")
            table_service_client.create_table(table)

    print("~ ~ Writing container configurations...")

    container_config_table = ContainerConfigTable(
        lambda: (
            None,
            table_service_client.get_table_client(DEFAULT_CONTAINER_CONFIG_TABLE_NAME),
        )
    )
    with open(CONTAINER_CONFIG_PATH) as f:
        js = json.load(f)
    for container_path, config_dict in js.items():
        sa, container = container_path.split("/")
        container_config_table.set_config(sa, container, ContainerConfig(**config_dict))

    print("~ ~ Writing collection configurations...")

    collection_config_table = CollectionConfigTable(
        lambda: (
            None,
            table_service_client.get_table_client(DEFAULT_COLLECTION_CONFIG_TABLE_NAME),
        )
    )
    with open(COLLECTION_CONFIG_PATH) as f:
        js = json.load(f)
    for collection_id, config_dict in js.items():
        config = CollectionConfig(**config_dict)
        collection_config_table.set_config(collection_id, config)

    print("~ ~ Writing ip exceptions...")

    ip_config_table = IPExceptionListTable(
        lambda: (
            None,
            table_service_client.get_table_client(
                DEFAULT_IP_EXCEPTION_CONFIG_TABLE_NAME
            ),
        )
    )
    ip_config_table.add_exception("127.0.0.1")

    # Blob

    blob_service_client: BlobServiceClient = BlobServiceClient.from_connection_string(
        AZURITE_CONNECT_STRING
    )
    containers = [c.name for c in blob_service_client.list_containers()]
    for container in ["output"]:
        if container not in containers:
            print(f"~ ~ Creating container {container}...")
            blob_service_client.create_container(container)

    print("~ Done Azurite setup.")


if __name__ == "__main__":
    setup_azurite()
