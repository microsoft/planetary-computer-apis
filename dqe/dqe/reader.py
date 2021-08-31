from typing import List

import planetary_computer as pc
from cogeo_mosaic.backends import SQLiteBackend
from rio_tiler.io.stac import STACReader

from pqecommon.render import COLLECTION_RENDER_CONFIG, BlobCDN


class PCSTACReader(STACReader):
    def _get_asset_url(self, asset: str) -> str:
        asset_url = BlobCDN.transform_if_available(super()._get_asset_url(asset))

        if self.item.collection_id:
            render_config = COLLECTION_RENDER_CONFIG.get(self.item.collection_id)
            if render_config and render_config.requires_token:
                asset_url = pc.sign(asset_url)

        return asset_url


class PCSQLiteMosaicBackend(SQLiteBackend):
    def get_assets(self, x: int, y: int, z: int) -> List[str]:
        # Ensure we're not reading from a low zoom level,
        # as that can really gum things up.
        if z < self.minzoom:
            return []

        return [BlobCDN.transform_if_available(x) for x in super().get_assets(x, y, z)]
