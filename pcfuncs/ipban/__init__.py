import datetime
import logging

import azure.functions as func
from azure.data.tables import TableServiceClient
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient

from .config import settings
from .models import UpdateBannedIPTask

logger = logging.getLogger(__name__)


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp: str = (
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    )
    logger.info("Updating the ip ban list at %s", utc_timestamp)
    credential: DefaultAzureCredential = DefaultAzureCredential()
    with LogsQueryClient(credential) as logs_query_client, TableServiceClient(
        endpoint=settings.storage_account_url, credential=credential
    ) as table_service_client, table_service_client.create_table_if_not_exists(
        settings.banned_ip_table
    ) as table_client:
        task = UpdateBannedIPTask(logs_query_client, table_client)
        task.run()
