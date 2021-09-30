"""Common logging setup, in order to have the same logging functionality
across all services
"""

import logging
import sys
from typing import Optional
from urllib.parse import urlparse

from fastapi import Request
from opencensus.ext.azure.log_exporter import AzureLogHandler

from pqecommon.config import CommonConfig


# Custom filter that outputs custom_dimensions, only if present
class OptionalCustomDimensionsFilter(logging.Formatter):
    def __init__(
        self,
        message_fmt: Optional[str],
        dt_fmt: Optional[str],
        service_name: Optional[str],
    ):
        logging.Formatter.__init__(self, message_fmt, dt_fmt)
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        if "custom_dimensions" not in record.__dict__:
            record.__dict__["custom_dimensions"] = ""
        else:
            # Add the service name to custom_dimensions, so it's queryable
            record.__dict__["custom_dimensions"]["service"] = self.service_name
        return super().format(record)


# Log filter for Azure-targeted messages (containing custom_dimensions)
class CustomDimensionsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return bool(record.__dict__["custom_dimensions"])


# Initialize logging, including a console handler, and sending all logs containing
# custom_dimensions to Application Insights
def init_logging(service_name: str) -> None:
    config = CommonConfig.from_environment()

    # Setup logging
    log_level = logging.DEBUG if config.debug else logging.INFO
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Console log handler
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setLevel(log_level)
    formatter = OptionalCustomDimensionsFilter(
        "[%(levelname)s] %(asctime)s - %(message)s %(custom_dimensions)s",
        None,
        service_name,
    )
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)

    # Azure log handler
    instrumentation_key = config.app_insights_instrumentation_key
    if instrumentation_key:
        azure_handler = AzureLogHandler(
            connection_string=f"InstrumentationKey={instrumentation_key}"
        )
        azure_handler.addFilter(CustomDimensionsFilter())
        logger.addHandler(azure_handler)
    else:
        logger.info("Not adding Azure log handler since no instrumentation key defined")


def log_collection_request(
    domain: str,
    logger: logging.Logger,
    collection_id: Optional[str],
    item_id: Optional[str],
    request: Request,
) -> None:
    logger.info(
        f"{domain} request for collection {collection_id}",
        extra={
            "custom_dimensions": dict(
                [
                    (k, v)
                    for k, v in {
                        "collection_id": collection_id,
                        "item_id": item_id,
                        "url": f"{request.url}",
                        "service_name": domain,
                    }.items()
                    if v is not None
                ]
            )
        },
    )


def request_to_path(request: Request) -> str:
    parsed_url = urlparse(f"{request.url}")
    return parsed_url.path
