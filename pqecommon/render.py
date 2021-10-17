import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pqecommon.utils import get_param_str


@dataclass
class DefaultRenderConfig:
    """
    A class used to represent information convenient for accessing
    the rendered assets of a collection.

    The parameters stored by this class are not the only parameters
    by which rendering is possible or useful but rather represent the
    most convenient renderings for human consumption and preview.
    For example, if a TIF asset can be viewed as an RGB approximating
    normal human vision, parameters will likely encode this rendering.
    """

    assets: List[str]
    render_params: Dict[str, Any]
    minzoom: int
    maxzoom: Optional[int] = 18
    create_links: bool = True
    has_mosaic: bool = False
    mosaic_preview_zoom: Optional[int] = None
    mosaic_preview_coords: Optional[List[float]] = None
    requires_token: bool = False
    hidden: bool = False  # Hide from API

    def get_assets_param(self) -> str:
        return ",".join(self.assets)

    def get_render_params(self) -> str:
        return get_param_str(self.render_params)

    @property
    def should_add_collection_links(self) -> bool:
        return self.has_mosaic and self.create_links and (not self.hidden)

    @property
    def should_add_item_links(self) -> bool:
        return self.create_links and (not self.hidden)


# TODO: Should store this in the PQE database as a separate
# table of PC-specific configuration per collection


COLLECTION_RENDER_CONFIG = {
    "3dep-seamless": DefaultRenderConfig(
        assets=["data"],
        render_params={"colormap_name": "terrain", "rescale": [-1000, 4000]},
        has_mosaic=True,
        requires_token=True,
        mosaic_preview_zoom=8,
        mosaic_preview_coords=[47.1113, -120.8578],
        minzoom=8,
    ),
    "alos-dem": DefaultRenderConfig(
        assets=["data"],
        render_params={"colormap_name": "terrain", "rescale": [-1000, 4000]},
        has_mosaic=True,
        mosaic_preview_zoom=8,
        mosaic_preview_coords=[35.6837, 138.4281],
        requires_token=True,
        minzoom=8,
    ),
    "aster-l1t": DefaultRenderConfig(
        assets=["VNIR"],
        render_params={"bidx": [2, 3, 1], "nodata": 0},
        has_mosaic=True,
        mosaic_preview_zoom=9,
        mosaic_preview_coords=[37.2141, -104.2947],
        minzoom=9,
    ),
    "cop-dem-glo-30": DefaultRenderConfig(
        assets=["data"],
        render_params={"colormap_name": "terrain", "rescale": [-1000, 4000]},
        has_mosaic=True,
        mosaic_preview_zoom=8,
        mosaic_preview_coords=[30.0572, 80.1735],
        requires_token=True,
        minzoom=8,
    ),
    "cop-dem-glo-90": DefaultRenderConfig(
        assets=["data"],
        render_params={"colormap_name": "terrain", "rescale": [-1000, 4000]},
        has_mosaic=True,
        mosaic_preview_zoom=8,
        mosaic_preview_coords=[46.8776, 12.1444],
        requires_token=True,
        minzoom=8,
    ),
    "gap": DefaultRenderConfig(
        assets=["data"],
        render_params={"tile_format": "png", "colormap_name": "gap-lulc"},
        has_mosaic=True,
        mosaic_preview_zoom=7,
        mosaic_preview_coords=[26.7409, -80.9714],
        requires_token=False,
        minzoom=5,
    ),
    "goes-mcmip": DefaultRenderConfig(
        create_links=True,  # Issues with colormap size, rendering
        assets=["data"],
        render_params={"colormap_name": "gap-lulc"},
        has_mosaic=True,
        mosaic_preview_zoom=13,
        mosaic_preview_coords=[39.95340, -75.16333],
        requires_token=True,
        minzoom=6,
    ),
    "goes-cmi": DefaultRenderConfig(
        create_links=True,
        assets=["data"],
        render_params={
            "expression": (
                "C02_2km_wm,"
                "0.45*C02_2km_wm+0.1*C03_2km_wm+0.45*C01_2km_wm,"
                "C01_2km_wm"
            ),
            "nodata": -1,
            "rescale": [1, 1000],
            "color_formula": "Gamma RGB 2.5 Saturation 1.4 Sigmoidal RGB 2 0.7",
            "resampling": "bilinear",
        },
        has_mosaic=True,
        mosaic_preview_zoom=4,
        mosaic_preview_coords=[33.4872, -114.4842],
        requires_token=True,
        minzoom=2,
    ),
    "hgb": DefaultRenderConfig(
        assets=["aboveground"],
        render_params={"colormap_name": "greens", "nodata": 0, "rescale": [0, 255]},
        has_mosaic=True,
        mosaic_preview_zoom=9,
        mosaic_preview_coords=[-7.641129, 39.162521],
        minzoom=2,
    ),
    "hrea": DefaultRenderConfig(
        assets=["estimated-brightness"],
        render_params={"colormap_name": "magma", "rescale": [1, 200]},
        has_mosaic=True,
        mosaic_preview_zoom=3,
        mosaic_preview_coords=[11.8280, 20.6367],
        minzoom=3,
    ),
    "io-lulc": DefaultRenderConfig(
        assets=["data"],
        render_params={"colormap_name": "io-lulc"},
        has_mosaic=True,
        mosaic_preview_zoom=4,
        mosaic_preview_coords=[-0.8749, 109.8456],
        minzoom=4,
    ),
    "jrc-gsw": DefaultRenderConfig(
        assets=["occurrence"],
        render_params={"colormap_name": "jrc-occurrence", "nodata": 0},
        has_mosaic=True,
        mosaic_preview_zoom=10,
        mosaic_preview_coords=[24.21647, 91.015209],
        minzoom=4,
    ),
    "landsat-8-c2-l2": DefaultRenderConfig(
        assets=["SR_B4", "SR_B3", "SR_B2"],
        render_params={
            "color_formula": "gamma RGB 2.7, saturation 1.5, sigmoidal RGB 15 0.55"
        },
        has_mosaic=True,
        mosaic_preview_zoom=11,
        mosaic_preview_coords=[37.4069, 118.8188],
        requires_token=True,
        minzoom=8,
    ),
    "mobi": DefaultRenderConfig(
        create_links=False,  # Couldn't find good visualization
        assets=["SpeciesRichness_All"],
        render_params={"colormap_name": "magma", "nodata": 128, "rescale": "0,1"},
        has_mosaic=True,
        requires_token=True,
        mosaic_preview_zoom=4,
        mosaic_preview_coords=[37.3052, -85.8457],
        minzoom=3,
    ),
    "mtbs": DefaultRenderConfig(
        create_links=False,  # Issues with COG size and format
        assets=["burn-severity"],
        render_params={"colormap_name": "mtbs-severity"},
        has_mosaic=True,
        mosaic_preview_zoom=9,
        mosaic_preview_coords=[39.2234, -122.6932],
        minzoom=3,
    ),
    "naip": DefaultRenderConfig(
        assets=["image"],
        render_params={"bidx": [1, 2, 3]},
        has_mosaic=True,
        mosaic_preview_zoom=13,
        mosaic_preview_coords=[36.0891, -111.8577],
        minzoom=11,
    ),
    "nasadem": DefaultRenderConfig(
        assets=["elevation"],
        render_params={"colormap_name": "terrain", "rescale": [-100, 4000]},
        has_mosaic=True,
        mosaic_preview_zoom=7,
        mosaic_preview_coords=[-10.7270, -74.7620],
        requires_token=False,
        minzoom=7,
    ),
    "sentinel-2-l2a": DefaultRenderConfig(
        assets=["visual"],
        render_params={"bidx": [1, 2, 3], "nodata": 0},
        has_mosaic=True,
        mosaic_preview_zoom=9,
        mosaic_preview_coords=[-16.4940, 124.0274],
        requires_token=True,
        minzoom=9,
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
