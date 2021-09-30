import logging
from typing import Dict, Tuple
from urllib.parse import urlparse

from fastapi import Request

from sas.config import SASEndpointConfig
from sas.core.validation import is_valid_ip
from sas.errors import HREFParseError, InvalidIPError, NoForwardedForHeaderError

logger = logging.getLogger(__name__)

# Headers containing information about the requester's
# IP address. Checked in the order listed here.
X_AZURE_CLIENTIP = "X-Azure-ClientIP"
X_ORIGINAL_FORWARDED_FOR = "X-Original-Forwarded-For"
X_FORWARDED_FOR = "X-Forwarded-For"

# Headers containing user data from API Management
WITHIN_DATACENTER_HEADER = "X-Within-Datacenter"
HAS_SUBSCRIPTION_HEADER = "X-Has-Subscription"
SUBSCRIPTION_KEY_HEADER = "X-Subscription-Key"
USER_EMAIL_HEADER = "X-User-Email"

# Headers containing user data from API Management
WITHIN_DATACENTER_HEADER = "X-Within-Datacenter"
HAS_SUBSCRIPTION_HEADER = "X-Has-Subscription"


def parse_blob_href(href: str) -> Tuple[str, str]:
    try:
        parsed_url = urlparse(href.rstrip("/"))
        account_name = parsed_url.netloc.split(".")[0]
        [container_name, _] = parsed_url.path.lstrip("/").split("/", 1)

        return account_name, container_name
    except Exception as e:
        raise HREFParseError(href) from e


def has_subscription(request: Request) -> bool:
    """Determines whether or not this request has an authorized subscription"""
    return request.headers.get(HAS_SUBSCRIPTION_HEADER) == "true"


def in_datacenter(request: Request) -> bool:
    """Determines whether or not this request originated from the datacenter"""
    return request.headers.get(WITHIN_DATACENTER_HEADER) == "true"


def get_subscription_key(request: Request) -> str:
    """Retrieves the subscription key from headers"""
    return request.headers.get(SUBSCRIPTION_KEY_HEADER)


def get_user_email(request: Request) -> str:
    """Retrieves the user email from headers"""
    return request.headers.get(USER_EMAIL_HEADER)


def get_request_dimensions(request: Request) -> Dict[str, str]:
    """Retrieves some common information from the request to log to App Insights"""
    return {
        "request_ip": get_request_ip(request),
        "subscription_key": get_subscription_key(request),
        "user_email": get_user_email(request),
    }


def get_request_ip(request: Request) -> str:
    """Gets the IP address of the request.

    Note:
    It's not possible to get the true request client IP when running
    in the development environment for some OS's (e.g. Docker for
    Windows does not support host network_mode). So to aide
    testing, if the environment variable SAS_DEV_FOR_IP is set,
    this method will use that value. This is automatically set to
    the host IP in `scripts/server`.
    """
    config = SASEndpointConfig.from_environment()

    ip_header = (
        config.dev_for_ip
        or request.headers.get(X_AZURE_CLIENTIP)  # set by Front Door
        or request.headers.get(X_ORIGINAL_FORWARDED_FOR)
        or request.headers.get(X_FORWARDED_FOR)
    )

    if not ip_header:
        raise NoForwardedForHeaderError()

    # If multiple IPs, take the first one
    ip = ip_header.split(",")[0]

    if not is_valid_ip(ip):
        logger.warning(f"Invalid IP Address - {ip} from {ip_header}")
        raise InvalidIPError(ip)

    return ip
