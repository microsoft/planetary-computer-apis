# config.py
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    storage_account_url: str = Field(json_schema_extra={"env": "STORAGE_ACCOUNT_URL"})
    banned_ip_table: str = Field(json_schema_extra={"env": "BANNED_IP_TABLE"})
    log_analytics_workspace_id: str = Field(json_schema_extra={"env": "LOG_ANALYTICS_WORKSPACE_ID"})

    # Time and threshold settings
    time_window_in_hours: int = Field(default=24, json_schema_extra={"env": "TIME_WINDOW_IN_HOURS"})
    threshold_read_count_in_gb: int = Field(
        default=5120, json_schema_extra={"env": "THRESHOLD_READ_COUNT_IN_GB"}
    )


# Create a global settings instance
settings = Settings()  # type: ignore
