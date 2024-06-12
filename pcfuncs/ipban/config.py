# config.py
from pydantic import BaseSettings


class Settings(BaseSettings):
    # Constants related to Azure Table Storage
    storage_account_url: str = "https://pctapisstagingsa.table.core.windows.net/"
    banned_ip_table: str = "blobstoragebannedip"

    # Log Analytics Workspace: pc-api-loganalytics
    log_analytics_workspace_id: str = "78d48390-b6bb-49a9-b7fd-a86f6522e9c4"

    # Time and threshold settings
    time_window_in_hours: int = 24
    threshold_read_count_in_gb: int = 5120


# Create a global settings instance
settings = Settings()
