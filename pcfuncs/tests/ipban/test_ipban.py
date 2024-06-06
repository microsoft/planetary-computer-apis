import pytest
from azure.data.tables import TableClient, TableServiceClient, UpdateMode
from ipban.constants import *
from ipban.models import UpdateBannedIPTask

def print_table_entries(table_client: TableClient):
    print(f"Printing all entries in the table: {table_client.table_name}")
    entities = table_client.list_entities()
    for entity in entities:
        print(entity)

@pytest.fixture
def mock_clients(mocker):
    mock_response = mocker.MagicMock()
    expected_rows = [("192.168.1.1", 150)]
    mock_response.tables[0].rows = expected_rows
    mock_logs_query_client = mocker.MagicMock()
    mock_logs_query_client.query_workspace.return_value = mock_response

    STORAGE_ACCOUNT_URL = "http://127.0.0.1:10002/devstoreaccount1"
    STORAGE_ACCOUNT_KEY = "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
    CONNECTION_STRING = f"DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey={STORAGE_ACCOUNT_KEY};TableEndpoint={STORAGE_ACCOUNT_URL};"

    # Use Azurite for unit tests and populate the table with initial data
    table_service = TableServiceClient.from_connection_string(CONNECTION_STRING)
    table_client = table_service.create_table_if_not_exists(table_name=BANNED_IP_TABLE)
    entities = [
        {
            "PartitionKey": "192.168.1.1",
            "RowKey": "192.168.1.1",
            "ReadCount": 50,
            "Threshold": 100,
            "TimeWindow": 15,
        },
        {
            "PartitionKey": "192.168.1.2",
            "RowKey": "192.168.1.2",
            "ReadCount": 150,
            "Threshold": 150,
            "TimeWindow": 30,
        },
    ]
    for entity in entities:
        table_client.create_entity(entity)
    print("Populating the table")
    print_table_entries(table_client)
    yield mock_logs_query_client, table_client

    print("After tests are completed")
    print_table_entries(table_client)
    # Clear all entities from the table
    entities = list(table_client.list_entities())
    for entity in entities:
        table_client.delete_entity(
            partition_key=entity["PartitionKey"], row_key=entity["RowKey"]
        )

    print("After cleanup are completed")
    print_table_entries(table_client)


def test_update_banned_ip_task(mock_clients):
    mock_logs_query_client, table_client = mock_clients
    task: UpdateBannedIPTask = UpdateBannedIPTask(mock_logs_query_client, table_client)
    task.run()
    print("Test is done:")
    print_table_entries(table_client)

    # Fetch updated data from table to check assertions
    # updated_entity_1 = table_client.get_entity("192.168.1.1", "192.168.1.1")
    # updated_entity_3 = table_client.get_entity("192.168.1.3", "192.168.1.3")
    # assert updated_entity_1["ReadCount"] == 200
    # assert updated_entity_3["ReadCount"] == 300
