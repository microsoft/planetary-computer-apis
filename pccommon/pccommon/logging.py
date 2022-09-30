"""Common logging setup, in order to have the same logging functionality
across all services
"""

import logging
import sys
from typing import Optional, Tuple, cast
from urllib.parse import urlparse

from fastapi import Request
from opencensus.ext.azure.log_exporter import AzureLogHandler

from pccommon.config import get_apis_config
from pccommon.constants import (
    HTTP_METHOD,
    HTTP_PATH,
    HTTP_URL,
    QS_REQUEST_ENTITY,
    X_AZURE_REF,
    X_REQUEST_ENTITY,
)


class ServiceName:
    STAC = "stac"
    TILER = "tiler"


PACKAGES = {
    ServiceName.STAC: "pcstac",
    ServiceName.TILER: "pctiler",
}


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


# Prevent successful health check pings from being logged
class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if len(record.args) != 5:
            return True

        args = cast(Tuple[str, str, str, str, int], record.args)
        endpoint = args[2]
        status = args[4]
        if endpoint == "/_mgmt/ping" and status == 200:
            return False

        return True


# Initialize logging, including a console handler, and sending all logs containing
# custom_dimensions to Application Insights
def init_logging(service_name: str) -> None:
    config = get_apis_config()

    # Exclude health check endpoint pings from the uvicorn logs
    logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

    # Setup logging for current package and pccommon
    for package in [PACKAGES[service_name], "pccommon"]:
        logger = logging.getLogger(package)
        logger.setLevel(logging.INFO)

        # Console log handler that includes custom dimensions
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setLevel(logging.DEBUG)
        formatter = OptionalCustomDimensionsFilter(
            "[%(levelname)s] %(asctime)s - %(message)s %(custom_dimensions)s",
            None,
            service_name,
        )
        consoleHandler.setFormatter(formatter)
        logger.addHandler(consoleHandler)

        if config.debug:
            logger.setLevel(logging.DEBUG)

        # Azure log handler
        instrumentation_key = config.app_insights_instrumentation_key
        if instrumentation_key:
            azure_handler = AzureLogHandler(
                connection_string=f"InstrumentationKey={instrumentation_key}"
            )
            azure_handler.addFilter(CustomDimensionsFilter())

            logger.addHandler(azure_handler)
        else:
            logger.info(f"Azure log handler not attached: {package} (missing key)")


def request_to_path(request: Request) -> str:
    parsed_url = urlparse(f"{request.url}")
    return parsed_url.path


def get_request_entity(request: Request) -> str:
    """Get the request entity from the given request. If not present as a
    header, attempt to parse from the query string
    """
    return request.headers.get(X_REQUEST_ENTITY) or request.query_params.get(
        QS_REQUEST_ENTITY
    )


def get_custom_dimensions(dimensions: dict, request: Request) -> dict:
    """Merge the base dimensions with the given dimensions."""

    base_dimensions = {
        "ref_id": request.headers.get(X_AZURE_REF),
        "request_entity": get_request_entity(request),
        "service": request.app.state.service_name,
        HTTP_URL: str(request.url),
        HTTP_METHOD: str(request.method),
        HTTP_PATH: request_to_path(request),
    }
    base_dimensions.update(dimensions)
    return {"custom_dimensions": base_dimensions}
