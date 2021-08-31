import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pqecommon.utils import get_param_str


@dataclass
class DefaultRenderConfig:
    assets: List[str]
    render_params: Dict[str, Any]
    create_links: bool = True
    has_mosaic: bool = False
    mosaic_preview_zoom: Optional[int] = None
    mosaic_preview_coords: Optional[List[float]] = None
    requires_token: bool = False
    hidden: bool = False  # Hide from API

    def get_assets_param(self) -> str:
        return ",".join(self.assets)

    def get_render_param(self) -> str:
        return get_param_str(self.render_params)

    @property
    def should_add_collection_links(self) -> bool:
        return self.has_mosaic and self.create_links and (not self.hidden)

    @property
    def should_add_item_links(self) -> bool:
        return self.create_links and (not self.hidden)


# TODO HACK workaround until we have a better
# way to specify default titiler render params
# for a collection.
# Should store this in the PQE database as
# a separate table of PC-specific configuration
# per collection.


COLLECTION_RENDER_CONFIG = {
    "aster-l1t": DefaultRenderConfig(
        assets=["SWIR"],
        render_params={"bidx": [3, 2, 1], "nodata": 0},
        has_mosaic=False,
    ),
    "gap": DefaultRenderConfig(
        create_links=False,  # Issues with colormap size, rendering
        assets=["data"],
        render_params={"colormap_name": "gap-lulc"},
        has_mosaic=True,
        mosaic_preview_zoom=13,
        mosaic_preview_coords=[39.95340, -75.16333],
        requires_token=True,
    ),
    "hrea": DefaultRenderConfig(
        assets=["estimated-brightness"],
        render_params={"colormap_name": "magma", "rescale": [1, 256]},
        has_mosaic=True,
        mosaic_preview_zoom=9,
        mosaic_preview_coords=[30.79675, 31.1300348],
    ),
    "hgb": DefaultRenderConfig(
        assets=["aboveground"],
        render_params={"colormap_name": "greens", "nodata": 0, "rescale": [0, 255]},
        has_mosaic=True,
        mosaic_preview_zoom=9,
        mosaic_preview_coords=[-7.641129, 39.162521],
    ),
    "io-lulc": DefaultRenderConfig(
        assets=["data"],
        render_params={"colormap_name": "io-lulc"},
        has_mosaic=True,
        mosaic_preview_zoom=7,
        mosaic_preview_coords=[-4.1740, 109.40777],
    ),
    "jrc-gsw": DefaultRenderConfig(
        assets=["occurrence"],
        render_params={"colormap_name": "jrc-gsw", "nodata": 0},
        has_mosaic=True,
        mosaic_preview_zoom=10,
        mosaic_preview_coords=[24.21647, 91.015209],
    ),
    "landsat-8-c2-l2": DefaultRenderConfig(
        assets=["SR_B4", "SR_B3", "SR_B2"],
        render_params={},
        has_mosaic=False,
        requires_token=True,
    ),
    "mobi": DefaultRenderConfig(
        create_links=False,  # Couldn't find good visualization
        assets=["RSR_PollinatorInverts"],
        render_params={"colormap_name": "viridis", "nodata": 0},
        has_mosaic=True,
        requires_token=True,
        mosaic_preview_zoom=9,
        mosaic_preview_coords=[-7.641129, 39.162521],
    ),
    "mtbs": DefaultRenderConfig(
        create_links=False,  # Issues with COG size and format
        assets=["burn-severity"],
        render_params={"colormap_name": "magma", "rescale": [0, 255]},
        has_mosaic=True,
        mosaic_preview_zoom=15,
        mosaic_preview_coords=[39.95340, -75.16333],
    ),
    "naip": DefaultRenderConfig(
        assets=["image"],
        render_params={"bidx": [1, 2, 3]},
        has_mosaic=True,
        mosaic_preview_zoom=15,
        mosaic_preview_coords=[39.95340, -75.16333],
    ),
    "sentinel-2-l2a": DefaultRenderConfig(
        assets=["visual"],
        render_params={"bidx": [1, 2, 3], "nodata": 0},
        has_mosaic=False,
        requires_token=True,
    ),
}

STORAGE_ACCOUNTS_WITH_CDNS = set(["naipeuwest"])

BLOB_REGEX = re.compile(r".*/([^/]+?)\.blob\.core\.windows\.net.*")


class BlobCDN:
    @staticmethod
    def transform_if_available(asset_href: str) -> str:
        m = re.match(BLOB_REGEX, asset_href)
        if m:
            if m.group(1) in STORAGE_ACCOUNTS_WITH_CDNS:
                asset_href = asset_href.replace("blob.core.windows", "azureedge")

        return asset_href
