from typing import Any, Dict, List, Optional, Tuple, Type

import attr
import morecantile
import planetary_computer as pc
from cogeo_mosaic.errors import NoAssetFoundError
from fastapi import HTTPException
from geojson_pydantic import Polygon
from rio_tiler.errors import InvalidAssetName, MissingAssets, TileOutsideBounds
from rio_tiler.io.base import BaseReader
from rio_tiler.models import ImageData
from rio_tiler.mosaic import mosaic_reader
from titiler.pgstac import mosaic as pgstac_mosaic
from titiler.pgstac.settings import CacheSettings
from titiler.pgstac.reader import PgSTACReader
from pccommon.cdn import BlobCDN
from pccommon.config import get_render_config
from pctiler.reader_cog import CustomCOGReader  # type:ignore

cache_config = CacheSettings()


@attr.s
class ItemSTACReader(PgSTACReader):

    # TODO: remove CustomCOGReader once moved to rasterio 1.3
    reader: Type[BaseReader] = attr.ib(default=CustomCOGReader)

    def _get_asset_url(self, asset: str) -> str:
        asset_url = BlobCDN.transform_if_available(super()._get_asset_url(asset))

        if self.input.collection_id:
            render_config = get_render_config(self.input.collection_id)
            if render_config and render_config.requires_token:
                asset_url = pc.sign(asset_url)

        return asset_url


@attr.s
class MosaicSTACReader(pgstac_mosaic.CustomSTACReader):
    """Custom version of titiler.pgstac.mosaic.CustomSTACReader)."""

    def _get_asset_url(self, asset: str) -> str:
        """Validate asset names and return asset's url.

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

        return asset_url


@attr.s
class PGSTACBackend(pgstac_mosaic.PGSTACBackend):
    """PgSTAC Mosaic Backend."""

    reader: Type[MosaicSTACReader] = attr.ib(init=False, default=MosaicSTACReader)

    # Override from PGSTACBackend to use collection
    def assets_for_tile(
        self, x: int, y: int, z: int, collection: Optional[str] = None, **kwargs: Any
    ) -> List[Dict]:
        # Require a collection
        if not collection:
            raise HTTPException(
                status_code=422,
                detail="Tile request must contain a collection parameter.",
            )

        # Check that the zoom isn't lower than minZoom
        render_config = get_render_config(collection)
        if render_config and render_config.minzoom and render_config.minzoom > z:
            return []

        bbox = self.tms.bounds(morecantile.Tile(x, y, z))
        return self.get_assets(Polygon.from_bounds(*bbox), **kwargs)

    # override from PGSTACBackend to pass through collection
    def tile(
        self,
        tile_x: int,
        tile_y: int,
        tile_z: int,
        reverse: bool = False,
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

        if reverse:
            mosaic_assets = list(reversed(mosaic_assets))

        def _reader(
            item: Dict[str, Any], x: int, y: int, z: int, **kwargs: Any
        ) -> ImageData:
            with self.reader(
                item, tms=self.tms, **self.reader_options  # type: ignore
            ) as src_dst:
                return src_dst.tile(x, y, z, **kwargs)

        return mosaic_reader(
            mosaic_assets,
            _reader,
            tile_x,
            tile_y,
            tile_z,
            allowed_exceptions=(TileOutsideBounds, MissingAssets, InvalidAssetName),
            **kwargs,
        )
