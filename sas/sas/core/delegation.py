import logging
from datetime import datetime, timedelta
from typing import cast

import azure.core.exceptions
from azure.storage.blob import BlobServiceClient, UserDelegationKey
from cachetools import TTLCache, cached

from pqecommon.backoff import BackoffStrategy, with_backoff
from sas.config import SASEndpointConfig
from sas.errors import (
    NoServicePrincipleError,
    StorageAccountNotAuthorizedError,
    UserDelegationKeyError,
)

logger = logging.getLogger()


class UserDelegation:
    @classmethod
    @cached(cache=TTLCache(maxsize=100, ttl=60))  # type:ignore
    def get_key(cls, storage_account: str) -> UserDelegationKey:
        """Gets a user delegation key for the given storage account,
        if possible.
        """
        config = SASEndpointConfig.from_environment()

        if config.service_principle is None:
            logger.error(
                "[ERROR]  -- Environment variable credentials improperly configured"
            )
            raise NoServicePrincipleError()

        # Create a blob service client with the provided credentials. These
        # credentials must have the ability to create user delegation keys for
        # the target blob storage containers, for example, using the role:
        # "Storage Blob Data Contributor"
        credential = config.service_principle.get_credential()

        time_now = datetime.utcnow()
        key_start_time = time_now - timedelta(minutes=60)
        key_expiry_time = time_now + timedelta(minutes=60 * 24)

        # Obtain a user delegation key via the client
        try:
            with BlobServiceClient(
                account_url=f"https://{storage_account}.blob.core.windows.net",
                credential=credential,
            ) as client:

                return with_backoff(
                    lambda: cast(
                        UserDelegationKey,
                        client.get_user_delegation_key(  # type:ignore
                            key_start_time, key_expiry_time
                        ),
                    ),
                    strategy=BackoffStrategy(waits=[0.2, 0.4]),
                )

        except azure.core.exceptions.HttpResponseError as e:
            if e.status_code == 403:
                logger.error(
                    f"[WARN] -- Storage Account {storage_account} is not"
                    " authorized for user delegation tokens."
                )
                raise StorageAccountNotAuthorizedError(
                    "Endpoint is not authorized to generate SAS Tokens "
                    f"for {storage_account}"
                ) from e
            raise
        except azure.core.exceptions.ServiceRequestError:
            raise
        except Exception as e:
            logger.exception(e)
            raise UserDelegationKeyError(
                f"Unable to get user delegation key for {storage_account}"
            ) from e
