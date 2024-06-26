# config.py
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    storage_account_url: str = Field(env="STORAGE_ACCOUNT_URL")
    banned_ip_table: str = Field(env="BANNED_IP_TABLE")
    log_analytics_workspace_id: str = Field(env="LOG_ANALYTICS_WORKSPACE_ID")

    # Time and threshold settings
    time_window_in_hours: int = Field(default=24, env="TIME_WINDOW_IN_HOURS")
    threshold_read_count_in_gb: int = Field(
        default=5120, env="THRESHOLD_READ_COUNT_IN_GB"
    )


# Create a global settings instance
settings = Settings()  # type: ignore
