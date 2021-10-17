import logging
from datetime import datetime, timedelta, timezone

from azure.core.exceptions import ClientAuthenticationError
from azure.storage.blob import ContainerSasPermissions, generate_container_sas
from fastapi import Request
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module

from pqecommon.backoff import BackoffStrategy, with_backoff
from pqecommon.metrics import stats_recorder, view_manager
from sas.config import SASEndpointConfig
from sas.core.delegation import UserDelegation
from sas.core.models import SASToken
from sas.core.utils import (
    get_request_dimensions,
    get_request_ip,
    has_subscription,
    in_datacenter,
)
from sas.errors import SASError, SASTokenCreationError

logger = logging.getLogger(__name__)

_sas_token_metric_description = "how many SAS tokens have been created"

sas_token_creation_measure = measure_module.MeasureInt(
    "sas-token-creations",
    _sas_token_metric_description,
    "sas-token-creations",
)
sas_token_creation_view = view_module.View(
    "SAS token creation view",
    _sas_token_metric_description,
    ["container"],
    sas_token_creation_measure,
    aggregation_module.CountAggregation(),
)
if view_manager:
    view_manager.register_view(sas_token_creation_view)

# We are still experiencing failures with IP range restrictions,
# even when not applying them to in-datacenter IPs (which have
# a known issue in Azure Storage). This flag is set to False
# to avoid restricting IPs and therefore the errors that come
# from them.
RESTRICT_IPS = False


def _get_tag_map(container: str, request: Request) -> tag_map_module.TagMap:
    tmap = tag_map_module.TagMap()
    tmap.insert("container", container)
    return tmap


def get_sas_token(storage_account: str, container: str, request: Request) -> SASToken:
    """Generates a SAS Token for the given storage account and container

    This method will generate a SAS token with a variable expiry that
    is restricted to a requester IP address.
    """
    if stats_recorder:
        mmap = stats_recorder.new_measurement_map()
    else:
        mmap = None
    expiry = get_expiry(request)

    # Make the SAS token valid in the past to help prevent clock skew related issues
    start = (datetime.utcnow() - timedelta(days=1)).replace(
        microsecond=0, tzinfo=timezone.utc
    )

    ip = None
    if RESTRICT_IPS:
        # Only restrict by IP range for requests outside of the datacenter
        if not in_datacenter(request):
            ip = get_ip_range(request)

    common_dimensions = {
        **get_request_dimensions(request),
        "storage_account": storage_account,
        "container": container,
    }

    try:
        user_delegation_key = UserDelegation.get_key(storage_account)

        sas_token = SASToken(
            expiry=expiry.replace(microsecond=0),
            token=with_backoff(
                lambda: generate_container_sas(
                    account_name=storage_account,
                    container_name=container,
                    user_delegation_key=user_delegation_key,
                    permission=ContainerSasPermissions(read=True, list=True),
                    expiry=expiry,
                    start=start,
                    ip=ip,
                ),
                strategy=BackoffStrategy(waits=[0.2, 0.4]),
            ),
        )

        logger.info(
            "SAS Token generated",
            extra={
                "custom_dimensions": {
                    **common_dimensions,
                    "expiry": sas_token.expiry.isoformat(),
                }
            },
        )

        if mmap:
            mmap.measure_int_put(sas_token_creation_measure, 1)
            mmap.record(_get_tag_map(container, request))

        return sas_token

    except SASError:
        logger.error(
            "Could not create SAS token",
            extra={"custom_dimensions": common_dimensions},
        )
        raise
    except ClientAuthenticationError:
        logger.error(
            "Requested container not available",
            extra={"custom_dimensions": common_dimensions},
        )
        raise
    except Exception as e:
        raise SASTokenCreationError(
            f"Failed generating SAS token for {storage_account}/{container}"
        ) from e


def get_ip_range(request: Request) -> str:
    """Gets the IP range for which the SAS token will be restricted to."""
    ip = get_request_ip(request)

    # Generate the *.* range to allow
    base_parts = ip.split(".")[:2]
    range_min_parts = ["0", "0"]
    range_max_parts = ["255", "255"]
    ip_min = ".".join(base_parts + range_min_parts)
    ip_max = ".".join(base_parts + range_max_parts)

    return f"{ip_min}-{ip_max}"


def get_expiry(request: Request) -> datetime:
    """Gets the expiration data for a SAS token based on a request.

    The expiration is different depending on whether or not the request
    originated within the datacenter, and whether or not the user has a
    subscription.

    Returns a datetime with the UTC time zone set.
    """
    config = SASEndpointConfig.from_environment()
    expiry_minutes = config.expiry.get_expiry(
        in_datacenter=in_datacenter(request), has_subscription=has_subscription(request)
    )

    return (datetime.utcnow() + timedelta(minutes=expiry_minutes)).replace(
        microsecond=0, tzinfo=timezone.utc
    )
