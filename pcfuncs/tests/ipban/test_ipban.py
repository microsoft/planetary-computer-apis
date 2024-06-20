import logging
import uuid
from typing import Any, Generator, List, Tuple
from unittest.mock import MagicMock

import pytest
from azure.data.tables import TableClient, TableServiceClient
from azure.data.tables._entity import TableEntity
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient
from azure.monitor.query._models import LogsTableRow
from ipban.config import settings
from ipban.models import UpdateBannedIPTask
from pytest_mock import MockerFixture

MOCK_LOGS_QUERY_RESULT = [("192.168.1.1", 8000), ("192.168.1.4", 12000)]
TEST_ID = str(uuid.uuid4()).replace("-", "")  # dash is not allowed in table name
TEST_BANNED_IP_TABLE = f"testblobstoragebannedip{TEST_ID}"

logger = logging.getLogger(__name__)
PREPOPULATED_ENTITIES = [
    {
        "PartitionKey": "192.168.1.1",
        "RowKey": "192.168.1.1",
        "ReadCount": 647,
        "Threshold": settings.threshold_read_count_in_gb,
        "TimeWindow": settings.time_window_in_hours,
    },
    {
        "PartitionKey": "192.168.1.2",
        "RowKey": "192.168.1.2",
        "ReadCount": 214,
        "Threshold": settings.threshold_read_count_in_gb,
        "TimeWindow": settings.time_window_in_hours,
    },
    {
        "PartitionKey": "192.168.1.3",
        "RowKey": "192.168.1.3",
        "ReadCount": 550,
        "Threshold": settings.threshold_read_count_in_gb,
        "TimeWindow": settings.time_window_in_hours,
    },
]


def populate_banned_ip_table(table_client: TableClient) -> None:
    for entity in PREPOPULATED_ENTITIES:
        table_client.create_entity(entity)


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
    with TableServiceClient.from_connection_string(
        CONNECTION_STRING
    ) as table_service_client, table_service_client.create_table_if_not_exists(
        table_name=TEST_BANNED_IP_TABLE
    ) as table_client:
        # Pre-populate the banned ip table
        populate_banned_ip_table(table_client)
        yield logs_query_client, table_client

        # Delete the test table
        table_service_client.delete_table(TEST_BANNED_IP_TABLE)


@pytest.fixture
def integration_clients(
    mocker: MockerFixture,
) -> Generator[Tuple[LogsQueryClient, TableClient], Any, None]:
    credential: DefaultAzureCredential = DefaultAzureCredential()
    with LogsQueryClient(credential) as logs_query_client, TableServiceClient(
        endpoint=settings.storage_account_url, credential=credential
    ) as table_service_client, table_service_client.create_table_if_not_exists(
        TEST_BANNED_IP_TABLE
    ) as table_client:

        # Pre-populate the banned ip table
        populate_banned_ip_table(table_client)
        yield logs_query_client, table_client

        # Delete the test table
        table_service_client.delete_table(TEST_BANNED_IP_TABLE)


@pytest.mark.integration
def test_update_banned_ip_integration(
    integration_clients: Tuple[LogsQueryClient, TableClient]
) -> None:
    logger.info(f"Test id: {TEST_ID} - integration test is running")
    logs_query_client, table_client = integration_clients
    assert len(list(table_client.list_entities())) == len(PREPOPULATED_ENTITIES)
    task: UpdateBannedIPTask = UpdateBannedIPTask(logs_query_client, table_client)
    # retrieve the logs query result from pc-api-loganalytics
    logs_query_result: List[LogsTableRow] = task.run()
    assert len(list(table_client.list_entities())) == len(logs_query_result)
    for ip, expected_read_count in logs_query_result:
        entity: TableEntity = table_client.get_entity(ip, ip)
        assert entity["ReadCount"] == expected_read_count
        assert entity["Threshold"] == settings.threshold_read_count_in_gb
        assert entity["TimeWindow"] == settings.time_window_in_hours


def test_update_banned_ip(mock_clients: Tuple[MagicMock, TableClient]) -> None:
    logger.info(f"Test id: {TEST_ID} - unit test is running")
    mock_logs_query_client, table_client = mock_clients
    assert len(list(table_client.list_entities())) == len(PREPOPULATED_ENTITIES)
    task: UpdateBannedIPTask = UpdateBannedIPTask(mock_logs_query_client, table_client)
    task.run()
    assert len(list(table_client.list_entities())) == len(MOCK_LOGS_QUERY_RESULT)
    for ip, expected_read_count in MOCK_LOGS_QUERY_RESULT:
        entity = table_client.get_entity(ip, ip)
        assert entity["ReadCount"] == expected_read_count
        assert entity["Threshold"] == settings.threshold_read_count_in_gb
        assert entity["TimeWindow"] == settings.time_window_in_hours
