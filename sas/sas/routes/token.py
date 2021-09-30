import logging
from dataclasses import dataclass, field
from typing import Optional

from fastapi import APIRouter, Query, Request

from sas.collections import Collections
from sas.constants import API_KEY_DESCRIPTION
from sas.core.create import get_sas_token
from sas.core.models import SASToken
from sas.core.validation import is_valid_container
from sas.errors import InvalidStorageLocationError, SASError, generic_500

logger = logging.getLogger(__name__)


@dataclass
class SASTokenEndpointFactory:
    """SAS Token Endpoint Factory"""

    router: APIRouter = field(default_factory=APIRouter)

    def __post_init__(self) -> None:
        """Post Init: register route and configure specific options."""
        self.register_routes()

    def register_routes(self) -> None:
        @self.router.get(
            "/{collection_id}",
            response_model=SASToken,
            summary=(
                "generate a SAS token for Assets that belong to the "
                "given STAC Collection"
            ),
        )
        async def collection_token(
            collection_id: str,
            request: Request,
            _: Optional[str] = Query(
                None, alias="subscription-key", description=API_KEY_DESCRIPTION
            ),
        ) -> SASToken:
            """
            Generate a [SAS Token](https://docs.microsoft.com/en-us/azure/storage/common/storage-sas-overview#how-a-shared-access-signature-works)
            for the given Collection (e.g. landsat-8-c2-l2)
            """  # noqa
            try:
                collection = Collections.get_collection(collection_id)

                return get_sas_token(
                    collection.storage_account, collection.container, request
                )

            except SASError as e:
                logger.exception(e)
                raise e.to_http()
            except Exception as e:
                logger.exception(e)
                raise generic_500()

        @self.router.get(
            "/{storage_account}/{container}",
            response_model=SASToken,
            summary=(
                "generate a SAS Token for the given Azure Blob storage account "
                "and container."
            ),
        )
        async def container_token(
            request: Request,
            storage_account: str = Query(
                ...,
                description=(
                    "The name of the storage account in which the container resides"
                ),
            ),
            container: str = Query(
                ...,
                description=(
                    "The name of the container that holds data that will "
                    "be readable with the given SAS token."
                ),
            ),
            _: Optional[str] = Query(
                None, alias="subscription-key", description=API_KEY_DESCRIPTION
            ),
        ) -> SASToken:
            """
            Generate a [SAS Token](https://docs.microsoft.com/en-us/azure/storage/common/storage-sas-overview#how-a-shared-access-signature-works)
            for the given storage account and container. The storage account and container
            must be associated with a Planetary Computer dataset indexed by the STAC API.
            """  # noqa
            try:
                if not is_valid_container(storage_account, container):
                    raise InvalidStorageLocationError(
                        storage_account=storage_account, container=container
                    )

                return get_sas_token(storage_account, container, request)

            except SASError as e:
                logger.exception(e)
                raise e.to_http()
            except Exception as e:
                logger.exception(e)
                raise generic_500()


sas_token_endpoint_factory = SASTokenEndpointFactory()
