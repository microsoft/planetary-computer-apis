import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Type

import attr
import morecantile
import planetary_computer as pc
from cogeo_mosaic.errors import NoAssetFoundError
from fastapi import HTTPException
from geojson_pydantic import Polygon
from rio_tiler.errors import InvalidAssetName, MissingAssets, TileOutsideBounds
from rio_tiler.models import ImageData
from rio_tiler.mosaic import mosaic_reader
from rio_tiler.types import AssetInfo
from starlette.requests import Request
from titiler.core.dependencies import DefaultDependency
from titiler.pgstac import mosaic as pgstac_mosaic
from titiler.pgstac.reader import PgSTACReader
from titiler.pgstac.settings import CacheSettings

from pccommon.cdn import BlobCDN
from pccommon.config import get_render_config
from pccommon.logging import get_custom_dimensions
from pctiler.config import get_settings

logger = logging.getLogger(__name__)

cache_config = CacheSettings()


@dataclass(init=False)
class ReaderParams(DefaultDependency):
    """reader parameters."""

    request: Request = field(init=False)

    def __init__(self, request: Request):
        """Initialize ReaderParams"""
        self.request = request


@attr.s
class ItemSTACReader(PgSTACReader):

    # We make request an optional attribute to avoid re-writing
    # the whole list of attribute
    request: Optional[Request] = attr.ib(default=None)

    def _get_asset_info(self, asset: str) -> AssetInfo:
        """return asset's url."""
        info = super()._get_asset_info(asset)
        asset_url = BlobCDN.transform_if_available(info["url"])

        if self.input.collection_id:
            render_config = get_render_config(self.input.collection_id)
            if render_config and render_config.requires_token:
                asset_url = pc.sign(asset_url)

        info["url"] = asset_url
        return info


@attr.s
class MosaicSTACReader(pgstac_mosaic.CustomSTACReader):
    """Custom version of titiler.pgstac.mosaic.CustomSTACReader)."""

    # We make request an optional attribute to avoid re-writing
    # the whole list of attribute
    request: Optional[Request] = attr.ib(default=None)

    def _get_asset_info(self, asset: str) -> AssetInfo:
        """Validate asset names and return asset's info.

        Args:
            asset (str): STAC asset name.

        Returns:
            str: STAC asset href.

        """
        if asset not in self.assets:
            raise InvalidAssetName(f"{asset} is not valid")

        asset_url = BlobCDN.transform_if_available(self.input["assets"][asset]["href"])

        collection = self.input.get("collection", None)
        if collection:
            render_config = get_render_config(collection)
            if render_config and render_config.requires_token:
                asset_url = pc.sign(asset_url)

        info = AssetInfo(url=asset_url)
        if "file:header_size" in self.input["assets"][asset]:
            info["env"] = {
                "GDAL_INGESTED_BYTES_AT_OPEN": self.input["assets"][asset][
                    "file:header_size"
                ]
            }

        return info


@attr.s
class PGSTACBackend(pgstac_mosaic.PGSTACBackend):
    """PgSTAC Mosaic Backend."""

    reader: Type[MosaicSTACReader] = attr.ib(init=False, default=MosaicSTACReader)

    # We make request an optional attribute to avoid re-writing
    # the whole list of attribute
    request: Optional[Request] = attr.ib(default=None)

    # Override from PGSTACBackend to use collection
    def assets_for_tile(  # type: ignore
        self, x: int, y: int, z: int, collection: Optional[str] = None, **kwargs: Any
    ) -> List[Dict]:
        settings = get_settings()

        # Require a collection
        if not collection:
            raise HTTPException(
                status_code=422,
                detail="Tile request must contain a collection parameter.",
            )

        ts = time.perf_counter()
        render_config = get_render_config(collection)

        # Don't render if this collection is unconfigured
        if not render_config:
            return []

        # Check that the zoom isn't lower than minZoom
        if render_config.minzoom and render_config.minzoom > z:
            return []

        # Override items_limit via render config for collection
        max_items = (
            render_config.max_items_per_tile or settings.default_max_items_per_tile
        )
        asset_kwargs = {**kwargs, "items_limit": max_items}

        bbox = self.tms.bounds(morecantile.Tile(x, y, z))
        assets = self.get_assets(Polygon.from_bounds(*bbox), **asset_kwargs)

        logger.info(
            "Perf: Mosaic get assets for tile.",
            extra=get_custom_dimensions(
                {
                    "duration": f"{time.perf_counter() - ts:0.4f}",
                    "collection": collection,
                    "zxy": f"{z}/{x}/{y}",
                    "count": len(assets),
                },
                self.request,
            ),
        )
        return assets

    # override from PGSTACBackend to pass through collection
    def tile(  # type: ignore
        self,
        tile_x: int,
        tile_y: int,
        tile_z: int,
        collection: Optional[str] = None,
        scan_limit: Optional[int] = None,
        items_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        exitwhenfull: Optional[bool] = None,
        skipcovered: Optional[bool] = None,
        **kwargs: Any,
    ) -> Tuple[ImageData, List[str]]:
        """Get Tile from multiple observation."""
        mosaic_assets = self.assets_for_tile(
            tile_x,
            tile_y,
            tile_z,
            collection=collection,
            scan_limit=scan_limit,
            items_limit=items_limit,
            time_limit=time_limit,
            exitwhenfull=exitwhenfull,
            skipcovered=skipcovered,
        )

        if not mosaic_assets:
            raise NoAssetFoundError(
                f"No assets found for tile {tile_z}-{tile_x}-{tile_y}"
            )

        ts = time.perf_counter()

        def _reader(
            item: Dict[str, Any], x: int, y: int, z: int, **kwargs: Any
        ) -> ImageData:
            with self.reader(
                item, tms=self.tms, **self.reader_options  # type: ignore
            ) as src_dst:
                return src_dst.tile(x, y, z, **kwargs)

        tile = mosaic_reader(
            mosaic_assets,
            _reader,
            tile_x,
            tile_y,
            tile_z,
            allowed_exceptions=(TileOutsideBounds, MissingAssets, InvalidAssetName),
            **kwargs,
        )

        logger.info(
            "Perf: Mosaic read tile.",
            extra=get_custom_dimensions(
                {
                    "duration": f"{time.perf_counter() - ts:0.4f}",
                    "collection": collection,
                    "zxy": f"{tile_z}/{tile_x}/{tile_y}",
                    "count": len(mosaic_assets),
                },
                self.request,
            ),
        )

        return tile
