import logging
from dataclasses import dataclass, field
from typing import Optional, Union

from fastapi import APIRouter, Query, Request

from sas.constants import API_KEY_DESCRIPTION
from sas.core.create import get_sas_token
from sas.core.models import SignedLink, UnsignedLink
from sas.core.utils import get_request_dimensions, parse_blob_href
from sas.core.validation import is_blob_href, is_valid_container, is_valid_href
from sas.errors import (
    HREFParseError,
    InvalidStorageLocationError,
    SASError,
    generic_500,
)

logger = logging.getLogger(__name__)


@dataclass
class SASSignEndpointFactory:
    """SAS Sign Endpoint Factory"""

    router: APIRouter = field(default_factory=APIRouter)

    def __post_init__(self) -> None:
        """Post Init: register route and configure specific options."""
        self.register_routes()

    def register_routes(self) -> None:
        @self.router.get(
            "",
            response_model=Union[SignedLink, UnsignedLink],  # type:ignore
            summary="sign an HREF in the format of a URL and returns a SingedLink",
        )
        async def signed_href(
            request: Request,
            href: str = Query(..., description="HREF (URL) to sign"),
            _: Optional[str] = Query(
                None, alias="subscription-key", description=API_KEY_DESCRIPTION
            ),
        ) -> SignedLink:
            """
            Signs a HREF (a link URL) by appending a [SAS Token](https://docs.microsoft.com/en-us/azure/storage/common/storage-sas-overview#how-a-shared-access-signature-works).
            If the HREF is not a Azure Blob Storage HREF, then pass back the HREF unsigned.
            """  # noqa
            try:
                if not is_valid_href(href):
                    raise HREFParseError(href)

                if not is_blob_href(href):
                    # Not a blob HREF, so return unsigned.
                    return UnsignedLink(href=href)

                storage_account, container = parse_blob_href(href)

                common_dimensions = {
                    **get_request_dimensions(request),
                    "storage_account": storage_account,
                    "container": container,
                    "href": href,
                }

                if not is_valid_container(storage_account, container):
                    logger.warning(
                        "Invalid storage location",
                        extra={"custom_dimensions": common_dimensions},
                    )
                    raise InvalidStorageLocationError(
                        storage_account=storage_account, container=container
                    )

                sas_token = get_sas_token(storage_account, container, request)
                logger.info(
                    "Signed an HREF",
                    extra={
                        "custom_dimensions": {
                            **common_dimensions,
                            "expiry": sas_token.expiry.isoformat(),
                        }
                    },
                )
                return sas_token.sign(href)
            except SASError as e:
                logger.exception(e)
                raise e.to_http()
            except Exception as e:
                logger.exception(e)
                raise generic_500()


sas_sign_endpoint_factory = SASSignEndpointFactory()
