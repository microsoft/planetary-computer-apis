import os
from typing import Optional

from azure.storage.blob import ContainerClient
from pydantic_settings import BaseSettings

from pccommon.blob import get_container_client


class BaseExporterSettings(BaseSettings):
    api_root_url: str = "https://planetarycomputer.microsoft.com/api/data/v1"

    output_storage_url: str
    output_sas: Optional[str] = None
    output_account_key: Optional[str] = None

    def get_container_client(self) -> ContainerClient:
        return get_container_client(
            self.output_storage_url,
            sas_token=self.output_sas,
            account_key=self.output_account_key,
        )

    def get_register_url(self, data_api_url_override: Optional[str] = None) -> str:
        return os.path.join(
            data_api_url_override or self.api_root_url, "mosaic/register/"
        )

    def get_mosaic_info_url(
        self, collection_id: str, data_api_url_override: Optional[str] = None
    ) -> str:
        return os.path.join(
            data_api_url_override or self.api_root_url,
            f"mosaic/info?collection={collection_id}",
        )
