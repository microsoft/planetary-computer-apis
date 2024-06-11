from typing import Any, Dict, Generator, List, Tuple
from unittest.mock import MagicMock

from azure.data.tables._entity import TableEntity
import pytest
from azure.data.tables import TableClient, TableServiceClient
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient
from azure.monitor.query._models import (
    LogsTableRow,
)
from constants import (
    STORAGE_ACCOUNT_URL,
    THRESHOLD_READ_COUNT_IN_GB,
    TIME_WINDOW_IN_HOURS,
)
from ipban.models import UpdateBannedIPTask
from pytest_mock import MockerFixture

MOCK_LOGS_QUERY_RESULT = [("192.168.1.1", 170), ("192.168.1.4", 420)]
TEST_BANNED_IP_TABLE = "testBlobStorageBannedIp"


def populate_banned_ip_table(table_client: TableClient) -> List[Dict[str, Any]]:
    print("Populating the table")
    entities: List[Dict[str, Any]] = [
        {
            "PartitionKey": "192.168.1.1",
            "RowKey": "192.168.1.1",
            "ReadCount": 647,
            "Threshold": THRESHOLD_READ_COUNT_IN_GB,
            "TimeWindow": TIME_WINDOW_IN_HOURS,
        },
        {
            "PartitionKey": "192.168.1.2",
            "RowKey": "192.168.1.2",
            "ReadCount": 214,
            "Threshold": THRESHOLD_READ_COUNT_IN_GB,
            "TimeWindow": TIME_WINDOW_IN_HOURS,
        },
        {
            "PartitionKey": "192.168.1.3",
            "RowKey": "192.168.1.3",
            "ReadCount": 550,
            "Threshold": THRESHOLD_READ_COUNT_IN_GB,
            "TimeWindow": TIME_WINDOW_IN_HOURS,
        },
    ]
    for entity in entities:
        table_client.create_entity(entity)
    return entities


def clear_table(table_client: TableClient) -> None:
    entities = list(table_client.list_entities())
    for entity in entities:
        table_client.delete_entity(
            partition_key=entity["PartitionKey"], row_key=entity["RowKey"]
        )
    entities = list(table_client.list_entities())
    assert len(entities) == 0


@pytest.fixture
def mock_clients(
    mocker: MockerFixture,
) -> Generator[Tuple[MagicMock, TableClient], Any, None]:
    mock_response: MagicMock = mocker.MagicMock()
    mock_response.tables[0].rows = MOCK_LOGS_QUERY_RESULT
    logs_query_client: MagicMock = mocker.MagicMock()
    logs_query_client.query_workspace.return_value = mock_response
    CONNECTION_STRING: str = (
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsu"
        "Fq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
        "TableEndpoint=http://azurite:10002/devstoreaccount1;"
    )
    # Use Azurite for unit tests and populate the table with initial data
    table_service: TableServiceClient = TableServiceClient.from_connection_string(
        CONNECTION_STRING
    )
    table_client: TableClient = table_service.create_table_if_not_exists(
        table_name=TEST_BANNED_IP_TABLE
    )

    # Pre-populate the banned ip table
    populate_banned_ip_table(table_client)
    yield logs_query_client, table_client

    # Clear all entities from the table
    clear_table(table_client)


@pytest.fixture
def integration_clients(
    mocker: MockerFixture,
) -> Generator[Tuple[LogsQueryClient, TableClient], Any, None]:
    credential: DefaultAzureCredential = DefaultAzureCredential()
    logs_query_client: LogsQueryClient = LogsQueryClient(credential)
    table_service_client: TableServiceClient = TableServiceClient(
        endpoint=STORAGE_ACCOUNT_URL, credential=credential
    )
    table_client: TableClient = table_service_client.create_table_if_not_exists(
        TEST_BANNED_IP_TABLE
    )
    # Pre-populate the banned ip table
    populate_banned_ip_table(table_client)
    yield logs_query_client, table_client
    # Clear all entities from the table
    clear_table(table_client)


@pytest.mark.integration
def test_update_banned_ip_integration(
    integration_clients: Tuple[LogsQueryClient, TableClient]
) -> None:
    print("Integration test is running")
    logs_query_client, table_client = integration_clients
    task: UpdateBannedIPTask = UpdateBannedIPTask(logs_query_client, table_client)
    # retrieve the logs query result from pc-api-loganalytics
    logs_query_result: List[LogsTableRow] = task.run()
    entities = list(table_client.list_entities())
    assert len(logs_query_result) == len(entities)
    for ip, expected_read_count in logs_query_result:
        entity: TableEntity = table_client.get_entity(ip, ip)
        assert entity["ReadCount"] == expected_read_count
        assert entity["Threshold"] == THRESHOLD_READ_COUNT_IN_GB
        assert entity["TimeWindow"] == TIME_WINDOW_IN_HOURS


def test_update_banned_ip(mock_clients: Tuple[MagicMock, TableClient]) -> None:
    print("Unit test is running")
    mock_logs_query_client, table_client = mock_clients
    task: UpdateBannedIPTask = UpdateBannedIPTask(mock_logs_query_client, table_client)
    task.run()
    entities = list(table_client.list_entities())
    assert len(entities) == len(MOCK_LOGS_QUERY_RESULT)
    for ip, expected_read_count in MOCK_LOGS_QUERY_RESULT:
        entity = table_client.get_entity(ip, ip)
        assert entity["ReadCount"] == expected_read_count
        assert entity["Threshold"] == THRESHOLD_READ_COUNT_IN_GB
        assert entity["TimeWindow"] == TIME_WINDOW_IN_HOURS
