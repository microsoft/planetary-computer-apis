import datetime
import logging

import azure.functions as func
from azure.data.tables import TableClient, TableServiceClient
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient

from .constants import BANNED_IP_TABLE, STORAGE_ACCOUNT_URL
from .models import UpdateBannedIPTask


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp: str = (
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    )
    logging.info("Updating the ip ban list at %s", utc_timestamp)
    credential: DefaultAzureCredential = DefaultAzureCredential()
    logs_query_client: LogsQueryClient = LogsQueryClient(credential)
    table_service_client: TableServiceClient = TableServiceClient(
        endpoint=STORAGE_ACCOUNT_URL, credential=credential
    )
    table_client: TableClient = table_service_client.create_table_if_not_exists(
        BANNED_IP_TABLE
    )
    task: UpdateBannedIPTask = UpdateBannedIPTask(logs_query_client, table_client)
    task.run()
