# config.py
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    storage_account_url: str
    banned_ip_table: str
    log_analytics_workspace_id: str

    # Time and threshold settings
    time_window_in_hours: int = Field(default=24)
    threshold_read_count_in_gb: int = Field(default=5120)


# Create a global settings instance
settings = Settings()  # type: ignore
