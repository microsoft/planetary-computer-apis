import re
from ipaddress import ip_address
from urllib.parse import urlparse

from sas.collections import Collections

BLOB_STORAGE_DOMAIN = ".blob.core.windows.net"


url_regex = re.compile(
    r"^(?:http|ftp)s?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...  # noqa
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)
"""https://github.com/django/django/blob/stable/1.3.x/django/core/validators.py#L45"""


def is_valid_container(storage_account: str, container: str) -> bool:
    storage_set = Collections.get_storage_set()
    return storage_account in storage_set and container in storage_set[storage_account]


def is_valid_href(href: str) -> bool:
    return url_regex.search(href) is not None


def is_blob_href(href: str) -> bool:
    parsed_url = urlparse(href.rstrip("/"))
    return parsed_url.netloc.endswith(BLOB_STORAGE_DOMAIN)


def is_valid_ip(ip: str) -> bool:
    try:
        ip_address(ip)
        return True
    except ValueError:
        return False
