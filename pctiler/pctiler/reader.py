import json
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import attr
import morecantile
import planetary_computer as pc
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from cogeo_mosaic.errors import NoAssetFoundError
from fastapi import HTTPException
from geojson_pydantic import Point, Polygon
from rio_tiler.constants import WEB_MERCATOR_TMS, WGS84_CRS
from rio_tiler.errors import InvalidAssetName, MissingAssets, TileOutsideBounds
from rio_tiler.io.base import BaseReader, MultiBaseReader
from rio_tiler.io.cogeo import COGReader
from rio_tiler.io.stac import STACReader
from rio_tiler.models import ImageData
from rio_tiler.mosaic import mosaic_reader
from titiler.pgstac import mosaic as pgstac_mosaic
from titiler.pgstac.settings import CacheSettings

from pccommon.render import COLLECTION_RENDER_CONFIG, BlobCDN
from pctiler.reader_cog import CustomCOGReader  # type:ignore

cache_config = CacheSettings()


@attr.s
class ItemSTACReader(STACReader):

    # TODO: remove CustomCOGReader once moved to rasterio 1.3
    reader: Type[BaseReader] = attr.ib(default=CustomCOGReader)

    def _get_asset_url(self, asset: str) -> str:
        asset_url = BlobCDN.transform_if_available(super()._get_asset_url(asset))

        if self.item.collection_id:
            render_config = COLLECTION_RENDER_CONFIG.get(self.item.collection_id)
            if render_config and render_config.requires_token:
                asset_url = pc.sign(asset_url)

        return asset_url


@attr.s
class CustomSTACReader(MultiBaseReader):
    """Simplified STAC Reader.

    Items should be in form of:
    {
        "id": "IAMASTACITEM",
        "collection_id": "collection",
        "bbox": (0, 0, 10, 10),
        "assets": {
            "COG": {
                "href": "https://somewhereovertherainbow.io/cog.tif"
            }
        }
    }

    """
    input: Dict[str, Any] = attr.ib()
    tms: morecantile.TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)
    reader_options: Dict = attr.ib(factory=dict)

    reader: Type[BaseReader] = attr.ib(default=COGReader)

    minzoom: int = attr.ib(default=None)
    maxzoom: int = attr.ib(default=None)

    def __attrs_post_init__(self) -> None:
        """Set reader spatial infos and list of valid assets."""
        self.bounds = self.input["bbox"]
        self.crs = WGS84_CRS  # Per specification STAC items are in WGS84

        self.assets = list(self.input["assets"])

        if self.minzoom is None:
            self.minzoom = self.tms.minzoom

        if self.maxzoom is None:
            self.maxzoom = self.tms.maxzoom

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
            render_config = COLLECTION_RENDER_CONFIG.get(collection)
            if render_config and render_config.requires_token:
                asset_url = pc.sign(asset_url)

        return asset_url


@attr.s
class PGSTACBackend(pgstac_mosaic.PGSTACBackend):
    """PgSTAC Mosaic Backend."""

    reader: Type[CustomSTACReader] = attr.ib(init=False, default=CustomSTACReader)

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
        render_config = COLLECTION_RENDER_CONFIG.get(collection)
        if render_config and render_config.minzoom and render_config.minzoom > z:
            return []

        bbox = self.tms.bounds(morecantile.Tile(x, y, z))
        return self.get_assets(Polygon.from_bounds(*bbox), **kwargs)

    @cached(
        TTLCache(maxsize=cache_config.maxsize, ttl=cache_config.ttl),
        key=lambda self, geom, **kwargs: hashkey(self.path, str(geom), **kwargs),
    )
    def get_assets(
        self,
        geom: Union[Point, Polygon],
        fields: Optional[Dict[str, Any]] = None,
        scan_limit: Optional[int] = None,
        items_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        exitwhenfull: Optional[bool] = None,
        skipcovered: Optional[bool] = None,
    ) -> List[Dict]:
        """Find assets."""
        fields = fields or {
            "include": ["assets", "id", "bbox", "collection"],
        }

        scan_limit = scan_limit or 10000
        items_limit = items_limit or 100
        time_limit = time_limit or 10
        exitwhenfull = True if exitwhenfull is None else exitwhenfull
        skipcovered = True if skipcovered is None else skipcovered

        with self.pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM geojsonsearch(%s, %s, %s, %s, %s, %s, %s, %s);",
                    (
                        geom.json(exclude_none=True),
                        self.input,
                        json.dumps(fields),
                        scan_limit,
                        items_limit,
                        f"{time_limit} seconds",
                        exitwhenfull,
                        skipcovered,
                    ),
                )
                resp = cursor.fetchone()[0]

        return resp.get("features", [])

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
            with self.reader(item, tms=self.tms, **self.reader_options) as src_dst:
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
