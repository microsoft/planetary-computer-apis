import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from azure.identity import ClientSecretCredential

from pqecommon.config import CommonConfig

logger = logging.getLogger(__name__)


class EnvVars:
    # SAS token user delevation service principle credentials
    # These three environment variables must be set in order to generate a
    # SAS token. The associated service principal should have a role such as
    # "Storage Blob Data Contributor" for the containers that are to be accessed
    SAS_TENANT_ID = "SAS_TENANT_ID"
    SAS_CLIENT_ID = "SAS_CLIENT_ID"
    SAS_CLIENT_SECRET = "SAS_CLIENT_SECRET"

    # SAS token expiration durations
    SAS_EXPIRY_MINUTES_IN_DC = "SAS_EXPIRY_MINUTES_IN_DC"
    SAS_EXPIRY_MINUTES_OUT_OF_DC = "SAS_EXPIRY_MINUTES_OUT_OF_DC"
    SAS_EXPIRY_MINUTES_SUB_IN_DC = "SAS_EXPIRY_MINUTES_SUB_IN_DC"
    SAS_EXPIRY_MINUTES_SUB_OUT_OF_DC = "SAS_EXPIRY_MINUTES_SUB_OUT_OF_DC"

    # For development - allow users to set the IP to generate
    # SAS Tokens for as the headers forwarded from nginx are
    # on the docker network and not valid.
    SAS_DEV_FOR_IP = "SAS_DEV_FOR_IP"

    # This is the MQE endpoint that the SAS endpoint will pull
    # collection information from
    MQE_URL = "MQE_URL"


class ConfigError(Exception):
    pass


@dataclass
class ExpiryConfig:
    """Expiry times for SAS tokens. All values in minutes"""

    in_datacenter: int
    out_of_datacenter: int
    subscription_in_datacenter: int
    subscription_out_of_datacenter: int

    def get_expiry(self, in_datacenter: bool, has_subscription: bool) -> int:
        if in_datacenter:
            if has_subscription:
                return self.subscription_in_datacenter
            else:
                return self.in_datacenter
        else:
            if has_subscription:
                return self.subscription_out_of_datacenter
            else:
                return self.out_of_datacenter

    @classmethod
    def default(cls) -> "ExpiryConfig":
        return cls(
            in_datacenter=60,
            out_of_datacenter=5,
            subscription_in_datacenter=60 * 24 * 32,
            subscription_out_of_datacenter=60,
        )

    @classmethod
    def from_environment(cls) -> "ExpiryConfig":
        defaults = cls.default()

        def get_env_int(key: str) -> Optional[int]:
            value = os.getenv(key, None)
            if value is not None:
                try:
                    return int(value)
                except ValueError as e:
                    raise ConfigError(
                        f"Cannot parse environment variable {key} as int."
                    ) from e
            else:
                logger.warning(f"[WARN] -- {key} not set; using default value")
                return None

        return cls(
            in_datacenter=get_env_int(EnvVars.SAS_EXPIRY_MINUTES_IN_DC)
            or defaults.in_datacenter,
            out_of_datacenter=get_env_int(EnvVars.SAS_EXPIRY_MINUTES_OUT_OF_DC)
            or defaults.in_datacenter,
            subscription_in_datacenter=get_env_int(EnvVars.SAS_EXPIRY_MINUTES_SUB_IN_DC)
            or defaults.in_datacenter,
            subscription_out_of_datacenter=get_env_int(
                EnvVars.SAS_EXPIRY_MINUTES_SUB_OUT_OF_DC
            )
            or defaults.in_datacenter,
        )


@dataclass
class ServicePrincipleConfig:
    tenant: str
    client: str
    secret: str

    def get_credential(self) -> ClientSecretCredential:
        return ClientSecretCredential(
            tenant_id=self.tenant, client_id=self.client, client_secret=self.secret
        )

    @classmethod
    def from_environment(cls) -> Optional["ServicePrincipleConfig"]:
        env_tenant = os.getenv(EnvVars.SAS_TENANT_ID)
        env_client = os.getenv(EnvVars.SAS_CLIENT_ID)
        env_secret = os.getenv(EnvVars.SAS_CLIENT_SECRET)

        if env_tenant is None or env_client is None or env_secret is None:
            logger.warning(
                "[WARNING] -- SAS user delegation service "
                "principle information not in environment."
            )
            return None
        return cls(tenant=env_tenant, client=env_client, secret=env_secret)


@dataclass
class ApiSettings:
    title: str = "Planetary Computer Data Authentication API"
    openapi_url: str = "/openapi.json"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    api_version: str = "v1"
    mqe_url: str = os.environ[EnvVars.MQE_URL]


@dataclass
class SASEndpointConfig:
    api_settings: ApiSettings
    expiry: ExpiryConfig
    service_principle: Optional[ServicePrincipleConfig]
    dev_for_ip: Optional[str]
    monitoring: CommonConfig

    @classmethod
    @lru_cache
    def from_environment(cls) -> "SASEndpointConfig":
        dev_for_ip = os.getenv(EnvVars.SAS_DEV_FOR_IP)
        if dev_for_ip is not None:
            logger.warning(
                "[WARN] Forcing SAS tokens to be generated for "
                f"{dev_for_ip} for development"
            )
        return cls(
            api_settings=ApiSettings(),
            expiry=ExpiryConfig.from_environment(),
            service_principle=ServicePrincipleConfig.from_environment(),
            dev_for_ip=dev_for_ip,
            monitoring=CommonConfig.from_environment(),
        )
