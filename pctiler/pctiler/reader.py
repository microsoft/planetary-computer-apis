import logging
import time
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Type

import attr
import morecantile
import planetary_computer as pc
from cogeo_mosaic.errors import NoAssetFoundError
from fastapi import HTTPException
from geojson_pydantic import Polygon
from rio_tiler.errors import InvalidAssetName, MissingAssets, TileOutsideBounds
from rio_tiler.io.stac import STAC_ALTERNATE_KEY
from rio_tiler.models import ImageData
from rio_tiler.mosaic import mosaic_reader
from rio_tiler.types import AssetInfo
from starlette.requests import Request
from titiler.core.dependencies import DefaultDependency
from titiler.pgstac import backend as pgstac_mosaic
from titiler.pgstac.reader import PgSTACReader, SimpleSTACReader
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
        """Validate asset names and return asset's info.

        Args:
            asset (str): STAC asset name.

        Returns:
            AssetInfo: STAC asset info.

        """
        asset, vrt_options = self._parse_vrt_asset(asset)
        if asset not in self.assets:
            raise InvalidAssetName(
                f"'{asset}' is not valid, should be one of {self.assets}"
            )

        asset_info = self.item.assets[asset]
        extras = asset_info.extra_fields

        info = AssetInfo(
            url=asset_info.get_absolute_href() or asset_info.href,
            metadata=extras if not vrt_options else None,
        )

        if STAC_ALTERNATE_KEY and extras.get("alternate"):
            if alternate := extras["alternate"].get(STAC_ALTERNATE_KEY):
                info["url"] = alternate["href"]

        asset_url = BlobCDN.transform_if_available(info["url"])
        if self.item.collection_id:
            render_config = get_render_config(self.item.collection_id)
            if render_config and render_config.requires_token:
                asset_url = pc.sign(asset_url)

        info["url"] = asset_url

        if asset_info.media_type:
            info["media_type"] = asset_info.media_type

        # https://github.com/stac-extensions/file
        if head := extras.get("file:header_size"):
            info["env"] = {"GDAL_INGESTED_BYTES_AT_OPEN": head}

        # https://github.com/stac-extensions/raster
        if extras.get("raster:bands") and not vrt_options:
            bands = extras.get("raster:bands")
            stats = [
                (b["statistics"]["minimum"], b["statistics"]["maximum"])
                for b in bands
                if {"minimum", "maximum"}.issubset(b.get("statistics", {}))
            ]
            # check that stats data are all double and make warning if not
            if (
                stats
                and all(isinstance(v, (int, float)) for stat in stats for v in stat)
                and len(stats) == len(bands)
            ):
                info["dataset_statistics"] = stats
            else:
                warnings.warn(
                    "Some statistics data in STAC are invalid, they will be ignored."
                )

        if vrt_options:
            info["url"] = f"vrt://{info['url']}?{vrt_options}"

        return info


@attr.s
class MosaicSTACReader(SimpleSTACReader):
    """Custom version of titiler.pgstac.reader.SimpleSTACReader."""

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
        asset, vrt_options = self._parse_vrt_asset(asset)
        if asset not in self.assets:
            raise InvalidAssetName(
                f"{asset} is not valid. Should be one of {self.assets}"
            )

        asset_info = self.input["assets"][asset]
        info = AssetInfo(
            url=asset_info["href"],
            env={},
        )

        asset_url = BlobCDN.transform_if_available(info["url"])
        if collection := self.input.get("collection", None):
            render_config = get_render_config(collection)
            if render_config and render_config.requires_token:
                asset_url = pc.sign(asset_url)

        info["url"] = asset_url

        if media_type := asset_info.get("type"):
            info["media_type"] = media_type

        if header_size := asset_info.get("file:header_size"):
            info["env"]["GDAL_INGESTED_BYTES_AT_OPEN"] = header_size

        if bands := asset_info.get("raster:bands"):
            stats = [
                (b["statistics"]["minimum"], b["statistics"]["maximum"])
                for b in bands
                if {"minimum", "maximum"}.issubset(b.get("statistics", {}))
            ]
            if len(stats) == len(bands):
                info["dataset_statistics"] = stats

        if vrt_options:
            info["url"] = f"vrt://{info['url']}?{vrt_options}"

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
                self.request,  # type: ignore
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

        img, used_assets = mosaic_reader(
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
                self.request,  # type: ignore
            ),
        )

        return img, [x["id"] for x in used_assets]
