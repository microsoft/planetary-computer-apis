import re

from pccommon.config import CommonConfig

BLOB_REGEX = re.compile(r".*/([^/]+?)\.blob\.core\.windows\.net/([^/]+?).*")


class BlobCDN:
    @staticmethod
    def transform_if_available(asset_href: str) -> str:
        m = re.match(BLOB_REGEX, asset_href)
        if m:
            storage_account = m.group(1)
            container = m.group(2)
            config = (
                CommonConfig.from_environment()
                .get_container_config_table()
                .get_config(storage_account, container)
            )
            if config and config.has_cdn:
                asset_href = asset_href.replace("blob.core.windows", "azureedge")

        return asset_href
