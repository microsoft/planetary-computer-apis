import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)


class EnvVars:
    # DEBUG mode
    DEBUG = "DEBUG"

    # Application Insights instrumentation key for logging via OpenCensus
    APP_INSIGHTS_INSTRUMENTATION_KEY = "APP_INSIGHTS_INSTRUMENTATION_KEY"


@dataclass
class CommonConfig:
    app_insights_instrumentation_key: Optional[str]
    debug: bool = os.getenv(EnvVars.DEBUG, "False").lower() == "true"

    @classmethod
    @lru_cache
    def from_environment(cls) -> "CommonConfig":
        app_insights_instrumentation_key = os.getenv(
            EnvVars.APP_INSIGHTS_INSTRUMENTATION_KEY
        )
        if app_insights_instrumentation_key is None:
            logger.warning("App Insights Instumentation Key not in environment.")
        return cls(
            app_insights_instrumentation_key=app_insights_instrumentation_key,
        )
