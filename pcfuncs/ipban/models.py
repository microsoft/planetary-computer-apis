import datetime
import logging

import azure.functions as func
from azure.data.tables import TableClient, TableServiceClient, UpdateMode
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient
from .constants import *


class UpdateBannedIPTask:
    def __init__(
        self,
        logs_query_client: LogsQueryClient,
        table_client: TableClient,
    ):
        self.log_query_client = logs_query_client
        self.table_client = table_client

    def run(self):
        utc_timestamp = (
            datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
        )
        logging.info("Python timer trigger function ran at %s", utc_timestamp)
        query_result = self.get_blob_logs_query_result()
        self.update_banned_ips(query_result)

    def get_blob_logs_query_result(self):
        query = f"""
        StorageBlobLogs
        | where TimeGenerated > ago({TIME_WINDOW_IN_HOURS}h)
        | extend IpAddress = tostring(split(CallerIpAddress, ":")[0])
        | summarize readcount = sum(ResponseBodySize) / (1024 * 1024 * 1024) by IpAddress
        | where readcount > {THRESHOLD_READ_COUNT_IN_GB}
        """
        response = self.log_query_client.query_workspace(
            LOG_ANALYTICS_WORKSPACE_ID, query, timespan=None
        )
        return response.tables[0].rows

    def update_banned_ips(self, query_result):
        existing_ips = {
            entity["RowKey"]: entity for entity in self.table_client.list_entities()
        }
        print(existing_ips)
        result_ips = set()
        for result in query_result:
            ip_address, read_count = result[0], int(result[1])
            result_ips.add(ip_address)
            entity = {
                "PartitionKey": ip_address,
                "RowKey": ip_address,
                "ReadCount": read_count,
                "Threshold": THRESHOLD_READ_COUNT_IN_GB,
                "TimeWindow": TIME_WINDOW_IN_HOURS,
            }

            if ip_address in existing_ips:
                self.table_client.update_entity(entity, mode=UpdateMode.REPLACE)
            else:
                self.table_client.create_entity(entity)

        for ip_address in existing_ips:
            if ip_address not in result_ips:
                self.table_client.delete_entity(
                    partition_key=ip_address, row_key=ip_address
                )

        logging.info("Table sync complete.")
