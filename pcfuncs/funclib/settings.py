from typing import Optional
from urllib.parse import urlencode, urlsplit

from azure.storage.blob import ContainerClient
from funclib.errors import InvalidInputError
from pydantic_settings import BaseSettings

from pccommon.blob import get_container_client


class BaseExporterSettings(BaseSettings):
    api_root_url: str = "https://planetarycomputer.microsoft.com/api/data/v1"
    output_storage_url: str

    def get_container_client(self) -> ContainerClient:
        return get_container_client(
            self.output_storage_url,
        )

    def get_register_url(self, data_api_url_override: Optional[str] = None) -> str:
        return f"{self.get_api_root_url(data_api_url_override)}/mosaic/register/"

    def get_api_root_url(self, data_api_url_override: Optional[str] = None) -> str:
        root = self.api_root_url.rstrip("/")
        if (
            data_api_url_override is not None
            and data_api_url_override.rstrip("/") != root
        ):
            raise InvalidInputError(
                "data_api_url must match the server-configured API root URL."
            )
        return root

    def validate_api_url(self, url: str) -> str:
        try:
            target = urlsplit(url)
            trusted = urlsplit(self.api_root_url)
            valid = (
                target.scheme in ("http", "https")
                and target.scheme == trusted.scheme
                and target.hostname == trusted.hostname
                and target.port == trusted.port
                and target.username is None
                and target.password is None
                and not target.fragment
                and not any(c.isspace() or ord(c) < 32 or c == "\\" for c in url)
            )
        except ValueError as e:
            raise InvalidInputError("Invalid data API response URL.") from e
        if not valid:
            raise InvalidInputError(
                "Data API response URLs must use the server-configured API origin."
            )
        return url

    def get_mosaic_info_url(
        self, collection_id: str, data_api_url_override: Optional[str] = None
    ) -> str:
        root = self.get_api_root_url(data_api_url_override)
        return f"{root}/mosaic/info?{urlencode({'collection': collection_id})}"
