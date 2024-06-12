import logging
from typing import Any, List, Set

from azure.data.tables import TableClient, UpdateMode
from azure.monitor.query import LogsQueryClient
from azure.monitor.query._models import LogsTableRow

from .constants import (
    LOG_ANALYTICS_WORKSPACE_ID,
    THRESHOLD_READ_COUNT_IN_GB,
    TIME_WINDOW_IN_HOURS,
)


class UpdateBannedIPTask:
    def __init__(
        self,
        logs_query_client: LogsQueryClient,
        table_client: TableClient,
    ) -> None:
        self.log_query_client = logs_query_client
        self.table_client = table_client

    def run(self) -> List[LogsTableRow]:
        query_result: List[LogsTableRow] = self.get_blob_logs_query_result()
        self.update_banned_ips(query_result)
        return query_result

    def get_blob_logs_query_result(self) -> List[LogsTableRow]:
        query: str = f"""
        StorageBlobLogs
        | where TimeGenerated > ago({TIME_WINDOW_IN_HOURS}h)
        | extend IpAddress = tostring(split(CallerIpAddress, ":")[0])
        | summarize readcount = sum(ResponseBodySize) / (1024 * 1024 * 1024)
        by IpAddress
        | where readcount > {THRESHOLD_READ_COUNT_IN_GB}
        """
        response: Any = self.log_query_client.query_workspace(
            LOG_ANALYTICS_WORKSPACE_ID, query, timespan=None
        )
        return response.tables[0].rows

    def update_banned_ips(self, query_result: List[LogsTableRow]) -> None:
        existing_ips = {
            entity["RowKey"]: entity for entity in self.table_client.list_entities()
        }
        result_ips: Set[str] = set()
        for result in query_result:
            ip_address: str = result[0]
            read_count: int = int(result[1])
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

        logging.info("IP ban list has been updated successfully")
