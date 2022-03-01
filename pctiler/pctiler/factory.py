# mypy: ignore-errors
from dataclasses import dataclass
from typing import Dict, Optional, Union
from urllib.parse import urlencode

import rasterio
from fastapi import Body, Depends, Path, Query, Request, Response
from geojson_pydantic.features import Feature, FeatureCollection
from geojson_pydantic.geometries import Polygon
from morecantile import TileMatrixSet
from rio_tiler.models import BandStatistics, Bounds, Info
from rio_tiler.utils import get_array_statistics
from starlette.templating import Jinja2Templates
from titiler.core.factory import MultiBaseTilerFactory, img_endpoint_params
from titiler.core.models.mapbox import TileJSON
from titiler.core.models.responses import (
    InfoGeoJSON,
    Point,
    Statistics,
    StatisticsGeoJSON,
)
from titiler.core.resources.enums import ImageType, MediaType, OptionalHeader
from titiler.core.resources.responses import GeoJSONResponse, JSONResponse, XMLResponse
from titiler.core.utils import Timer

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore

# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(
    directory=str(resources_files(__package__) / "templates")
)  # type: ignore


@dataclass
class PGMultiBaseTilerFactory(MultiBaseTilerFactory):

    ############################################################################
    # /bounds
    ############################################################################
    def bounds(self) -> None:
        """Register /bounds endpoint."""

        @self.router.get(
            "/bounds",
            response_model=Bounds,
            responses={200: {"description": "Return dataset's bounds."}},
        )
        def bounds(request: Request, src_path=Depends(self.path_dependency)) -> dict:
            """Return the bounds of the COG."""
            pool = request.app.state.dbpool
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    item_id=src_path["item"],
                    collection_id=src_path["collection"],
                    pool=pool,
                ) as src_dst:
                    return {"bounds": src_dst.geographic_bounds}

    ############################################################################
    # /info
    ############################################################################
    def info(self) -> None:
        """Register /info endpoint."""

        @self.router.get(
            "/info",
            response_model=Info,
            response_model_exclude_none=True,
            response_class=JSONResponse,
            responses={200: {"description": "Return dataset's basic info."}},
        )
        def info(request: Request, src_path=Depends(self.path_dependency)) -> dict:
            """Return dataset's basic info."""
            pool = request.app.state.dbpool
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    item_id=src_path["item"],
                    collection_id=src_path["collection"],
                    pool=pool,
                ) as src_dst:
                    return src_dst.info()

        @self.router.get(
            "/info.geojson",
            response_model=InfoGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/geo+json": {}},
                    "description": "Return dataset's basic info as a GeoJSON feature.",
                }
            },
        )
        def info_geojson(
            request: Request, src_path=Depends(self.path_dependency)
        ) -> dict:
            """Return dataset's basic info as a GeoJSON feature."""
            pool = request.app.state.dbpool
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    item_id=src_path["item"],
                    collection_id=src_path["collection"],
                    pool=pool,
                ) as src_dst:
                    return Feature(
                        geometry=Polygon.from_bounds(*src_dst.geographic_bounds),
                        properties=src_dst.info(),
                    )

    ############################################################################
    # /statistics
    ############################################################################
    def statistics(self) -> None:
        """add statistics endpoints."""

        # GET endpoint
        @self.router.get(
            "/statistics",
            response_class=JSONResponse,
            response_model=Statistics,
            responses={
                200: {
                    "content": {"application/json": {}},
                    "description": "Return dataset's statistics.",
                }
            },
        )
        def statistics(
            request: Request,
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
        ) -> dict:
            """Create image from a geojson feature."""
            pool = request.app.state.dbpool
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    item_id=src_path["item"],
                    collection_id=src_path["collection"],
                    pool=pool,
                ) as src_dst:
                    return src_dst.statistics(
                        **layer_params,
                        **image_params,
                        **dataset_params,
                        **stats_params,
                        hist_options={**histogram_params},
                    )

        # POST endpoint
        @self.router.post(
            "/statistics",
            response_model=StatisticsGeoJSON,
            response_model_exclude_none=True,
            response_class=GeoJSONResponse,
            responses={
                200: {
                    "content": {"application/json": {}},
                    "description": "Return dataset's statistics.",
                }
            },
        )
        def geojson_statistics(
            request: Request,
            geojson: Union[FeatureCollection, Feature] = Body(
                ..., description="GeoJSON Feature or FeatureCollection."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_dependency),
            stats_params=Depends(self.stats_dependency),
            histogram_params=Depends(self.histogram_dependency),
        ) -> dict:
            """Get Statistics from a geojson feature or featureCollection."""
            pool = request.app.state.dbpool
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    item_id=src_path["item"],
                    collection_id=src_path["collection"],
                    pool=pool,
                ) as src_dst:
                    # TODO: stream features for FeatureCollection
                    if isinstance(geojson, FeatureCollection):
                        for feature in geojson:
                            data = src_dst.feature(
                                feature.dict(exclude_none=True),
                                **layer_params,
                                **image_params,
                                **dataset_params,
                            )
                            stats = get_array_statistics(
                                data.as_masked(),
                                **stats_params,
                                **histogram_params,
                            )

                        feature.properties = feature.properties or {}
                        feature.properties.update(
                            {
                                "statistics": {
                                    f"{data.band_names[ix]}": BandStatistics(
                                        **stats[ix]
                                    )
                                    for ix in range(len(stats))
                                }
                            }
                        )

                    else:  # simple feature
                        data = src_dst.feature(
                            geojson.dict(exclude_none=True),
                            **layer_params,
                            **image_params,
                            **dataset_params,
                        )
                        stats = get_array_statistics(
                            data.as_masked(),
                            **stats_params,
                            **histogram_params,
                        )

                        geojson.properties = geojson.properties or {}
                        geojson.properties.update(
                            {
                                "statistics": {
                                    f"{data.band_names[ix]}": BandStatistics(
                                        **stats[ix]
                                    )
                                    for ix in range(len(stats))
                                }
                            }
                        )

                    return geojson

    ############################################################################
    # /tiles
    ############################################################################
    def tile(self) -> None:  # noqa: C901
        """Register /tiles endpoint."""

        @self.router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}.{format}", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x", **img_endpoint_params
        )
        @self.router.get(
            r"/tiles/{TileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **img_endpoint_params,
        )
        def tile(
            request: Request,
            z: int = Path(..., ge=0, le=30, description="TMS tiles's zoom level"),
            x: int = Path(..., description="TMS tiles's column"),
            y: int = Path(..., description="TMS tiles's row"),
            tms: TileMatrixSet = Depends(self.tms_dependency),
            scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
            tile_buffer: Optional[float] = Query(
                None,
                gt=0,
                alias="buffer",
                title="Tile buffer.",
                description=(
                    "Buffer on each side of the given tile. It must be a "
                    "multiple of `0.5`. Output **tilesize** will be expanded "
                    "to `tilesize + 2 * tile_buffer` (e.g 0.5 = 257x257, 1.0 "
                    "= 258x258)."
                ),
            ),
        ) -> Response:
            """Create map tile from a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            tilesize = scale * 256

            pool = request.app.state.dbpool
            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                        item_id=src_path["item"],
                        collection_id=src_path["collection"],
                        tms=tms,
                        pool=pool,
                    ) as src_dst:
                        data = src_dst.tile(
                            x,
                            y,
                            z,
                            tilesize=tilesize,
                            tile_buffer=tile_buffer,
                            **layer_params,
                            **dataset_params,
                        )
                        dst_colormap = getattr(src_dst, "colormap", None)
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            if not format:
                format = ImageType.jpeg if data.mask.all() else ImageType.png

            with Timer() as t:
                image = data.post_process(**postprocess_params)
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                content = image.render(
                    img_format=format.driver,
                    colormap=colormap or dst_colormap,
                    **format.profile,
                    **render_params,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return Response(content, media_type=format.mediatype, headers=headers)

    def tilejson(self) -> None:  # noqa: C901
        """Register /tilejson.json endpoint."""

        @self.router.get(
            "/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        @self.router.get(
            "/{TileMatrixSetId}/tilejson.json",
            response_model=TileJSON,
            responses={200: {"description": "Return a tilejson"}},
            response_model_exclude_none=True,
        )
        def tilejson(
            request: Request,
            tms: TileMatrixSet = Depends(self.tms_dependency),
            src_path=Depends(self.path_dependency),
            tile_format: Optional[ImageType] = Query(
                None, description="Output image type. Default is auto."
            ),
            tile_scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            minzoom: Optional[int] = Query(
                None, description="Overwrite default minzoom."
            ),
            maxzoom: Optional[int] = Query(
                None, description="Overwrite default maxzoom."
            ),
            layer_params=Depends(self.layer_dependency),  # noqa
            dataset_params=Depends(self.dataset_dependency),  # noqa
            postprocess_params=Depends(self.process_dependency),  # noqa
            colormap=Depends(self.colormap_dependency),  # noqa
            render_params=Depends(self.render_dependency),  # noqa
            tile_buffer: Optional[float] = Query(  # noqa
                None,
                gt=0,
                alias="buffer",
                title="Tile buffer.",
                description=(
                    "Buffer on each side of the given tile. It must be a "
                    "multiple of `0.5`. Output **tilesize** will be expanded "
                    "to `tilesize + 2 * tile_buffer` (e.g 0.5 = 257x257, 1.0 = "
                    "258x258)."
                ),
            ),
        ) -> dict:
            """Return TileJSON document for a dataset."""
            route_params = {
                "z": "{z}",
                "x": "{x}",
                "y": "{y}",
                "scale": tile_scale,
                "TileMatrixSetId": tms.identifier,
            }
            if tile_format:
                route_params["format"] = tile_format.value
            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                tiles_url += f"?{urlencode(qs)}"

            pool = request.app.state.dbpool
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    item_id=src_path["item"],
                    collection_id=src_path["collection"],
                    tms=tms,
                    pool=pool,
                ) as src_dst:
                    return {
                        "bounds": src_dst.geographic_bounds,
                        "minzoom": minzoom if minzoom is not None else src_dst.minzoom,
                        "maxzoom": maxzoom if maxzoom is not None else src_dst.maxzoom,
                        "tiles": [tiles_url],
                    }

    def wmts(self) -> None:  # noqa: C901
        """Register /wmts endpoint."""

        @self.router.get("/WMTSCapabilities.xml", response_class=XMLResponse)
        @self.router.get(
            "/{TileMatrixSetId}/WMTSCapabilities.xml", response_class=XMLResponse
        )
        def wmts(
            request: Request,
            tms: TileMatrixSet = Depends(self.tms_dependency),
            src_path=Depends(self.path_dependency),
            tile_format: ImageType = Query(
                ImageType.png, description="Output image type. Default is png."
            ),
            tile_scale: int = Query(
                1, gt=0, lt=4, description="Tile size scale. 1=256x256, 2=512x512..."
            ),
            minzoom: Optional[int] = Query(
                None, description="Overwrite default minzoom."
            ),
            maxzoom: Optional[int] = Query(
                None, description="Overwrite default maxzoom."
            ),
            layer_params=Depends(self.layer_dependency),  # noqa
            dataset_params=Depends(self.dataset_dependency),  # noqa
            postprocess_params=Depends(self.process_dependency),  # noqa
            colormap=Depends(self.colormap_dependency),  # noqa
            render_params=Depends(self.render_dependency),  # noqa
        ) -> str:
            """OGC WMTS endpoint."""
            route_params = {
                "z": "{TileMatrix}",
                "x": "{TileCol}",
                "y": "{TileRow}",
                "scale": tile_scale,
                "format": tile_format.value,
                "TileMatrixSetId": tms.identifier,
            }
            tiles_url = self.url_for(request, "tile", **route_params)

            qs_key_to_remove = [
                "tilematrixsetid",
                "tile_format",
                "tile_scale",
                "minzoom",
                "maxzoom",
                "service",
                "request",
            ]
            qs = [
                (key, value)
                for (key, value) in request.query_params._list
                if key.lower() not in qs_key_to_remove
            ]
            if qs:
                tiles_url += f"?{urlencode(qs)}"

            pool = request.app.state.dbpool
            with rasterio.Env(**self.gdal_config):
                with self.reader(
                    item_id=src_path["item"],
                    collection_id=src_path["collection"],
                    tms=tms,
                    pool=pool,
                ) as src_dst:
                    bounds = src_dst.geographic_bounds
                    minzoom = minzoom if minzoom is not None else src_dst.minzoom
                    maxzoom = maxzoom if maxzoom is not None else src_dst.maxzoom

            tileMatrix = []
            for zoom in range(minzoom, maxzoom + 1):
                matrix = tms.matrix(zoom)
                tm = (
                    f"""
                        <TileMatrix>
                            <ows:Identifier>{matrix.identifier}</ows:Identifier>
                            <ScaleDenominator>{matrix.scaleDenominator}</ScaleDenominator>
                            <TopLeftCorner>{matrix.topLeftCorner[0]}"""
                    f"""{matrix.topLeftCorner[1]}</TopLeftCorner>
                            <TileWidth>{matrix.tileWidth}</TileWidth>
                            <TileHeight>{matrix.tileHeight}</TileHeight>
                            <MatrixWidth>{matrix.matrixWidth}</MatrixWidth>
                            <MatrixHeight>{matrix.matrixHeight}</MatrixHeight>
                        </TileMatrix>"""
                )
                tileMatrix.append(tm)

            return templates.TemplateResponse(
                "wmts.xml",
                {
                    "request": request,
                    "tiles_endpoint": tiles_url,
                    "bounds": bounds,
                    "tileMatrix": tileMatrix,
                    "tms": tms,
                    "title": "Cloud Optimized GeoTIFF",
                    "layer_name": "cogeo",
                    "media_type": tile_format.mediatype,
                },
                media_type=MediaType.xml.value,
            )

    ############################################################################
    # /point
    ############################################################################
    def point(self) -> None:
        """Register /point endpoints."""

        @self.router.get(
            r"/point/{lon},{lat}",
            response_model=Point,
            response_class=JSONResponse,
            responses={200: {"description": "Return a value for a point"}},
        )
        def point(
            request: Request,
            response: Response,
            lon: float = Path(..., description="Longitude"),
            lat: float = Path(..., description="Latitude"),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
        ) -> dict:
            """Get Point value for a dataset."""
            timings = []

            pool = request.app.state.dbpool
            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                        item_id=src_path["item"],
                        collection_id=src_path["collection"],
                        pool=pool,
                    ) as src_dst:
                        values = src_dst.point(
                            lon,
                            lat,
                            **layer_params,
                            **dataset_params,
                        )
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                response.headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return {"coordinates": [lon, lat], "values": values}

    ############################################################################
    # /preview (Optional)
    ############################################################################
    def preview(self) -> None:
        """Register /preview endpoint."""

        @self.router.get(r"/preview", **img_endpoint_params)
        @self.router.get(r"/preview.{format}", **img_endpoint_params)
        def preview(
            request: Request,
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            img_params=Depends(self.img_dependency),
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
        ) -> Response:
            """Create preview of a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            pool = request.app.state.dbpool
            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                        item_id=src_path["item"],
                        collection_id=src_path["collection"],
                        pool=pool,
                    ) as src_dst:
                        data = src_dst.preview(
                            **layer_params,
                            **img_params,
                            **dataset_params,
                        )
                        dst_colormap = getattr(src_dst, "colormap", None)
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            if not format:
                format = ImageType.jpeg if data.mask.all() else ImageType.png

            with Timer() as t:
                image = data.post_process(**postprocess_params)
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                content = image.render(
                    img_format=format.driver,
                    colormap=colormap or dst_colormap,
                    **format.profile,
                    **render_params,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return Response(content, media_type=format.mediatype, headers=headers)

    ############################################################################
    # /crop (Optional)
    ############################################################################
    def part(self) -> None:
        """Register /crop endpoint."""

        # GET endpoints
        @self.router.get(
            r"/crop/{minx},{miny},{maxx},{maxy}.{format}",
            **img_endpoint_params,
        )
        @self.router.get(
            r"/crop/{minx},{miny},{maxx},{maxy}/{width}x{height}.{format}",
            **img_endpoint_params,
        )
        def part(
            request: Request,
            minx: float = Path(..., description="Bounding box min X"),
            miny: float = Path(..., description="Bounding box min Y"),
            maxx: float = Path(..., description="Bounding box max X"),
            maxy: float = Path(..., description="Bounding box max Y"),
            format: ImageType = Query(..., description="Output image type."),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_dependency),
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
        ) -> Response:
            """Create image from part of a dataset."""
            timings = []
            headers: Dict[str, str] = {}

            pool = request.app.state.dbpool
            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                        item_id=src_path["item"],
                        collection_id=src_path["collection"],
                        pool=pool,
                    ) as src_dst:
                        data = src_dst.part(
                            [minx, miny, maxx, maxy],
                            **layer_params,
                            **image_params,
                            **dataset_params,
                        )
                        dst_colormap = getattr(src_dst, "colormap", None)
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                image = data.post_process(**postprocess_params)
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                content = image.render(
                    img_format=format.driver,
                    colormap=colormap or dst_colormap,
                    **format.profile,
                    **render_params,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return Response(content, media_type=format.mediatype, headers=headers)

        # POST endpoints
        @self.router.post(
            r"/crop",
            **img_endpoint_params,
        )
        @self.router.post(
            r"/crop.{format}",
            **img_endpoint_params,
        )
        @self.router.post(
            r"/crop/{width}x{height}.{format}",
            **img_endpoint_params,
        )
        def geojson_crop(
            request: Request,
            geojson: Feature = Body(..., description="GeoJSON Feature."),
            format: ImageType = Query(
                None, description="Output image type. Default is auto."
            ),
            src_path=Depends(self.path_dependency),
            layer_params=Depends(self.layer_dependency),
            dataset_params=Depends(self.dataset_dependency),
            image_params=Depends(self.img_dependency),
            postprocess_params=Depends(self.process_dependency),
            colormap=Depends(self.colormap_dependency),
            render_params=Depends(self.render_dependency),
        ) -> Response:
            """Create image from a geojson feature."""
            timings = []
            headers: Dict[str, str] = {}

            pool = request.app.state.dbpool
            with Timer() as t:
                with rasterio.Env(**self.gdal_config):
                    with self.reader(
                        item_id=src_path["item"],
                        collection_id=src_path["collection"],
                        pool=pool,
                    ) as src_dst:
                        data = src_dst.feature(
                            geojson.dict(exclude_none=True),
                            **layer_params,
                            **image_params,
                            **dataset_params,
                        )
                        dst_colormap = getattr(src_dst, "colormap", None)
            timings.append(("dataread", round(t.elapsed * 1000, 2)))

            with Timer() as t:
                image = data.post_process(**postprocess_params)
            timings.append(("postprocess", round(t.elapsed * 1000, 2)))

            if not format:
                format = ImageType.jpeg if data.mask.all() else ImageType.png

            with Timer() as t:
                content = image.render(
                    img_format=format.driver,
                    colormap=colormap or dst_colormap,
                    **format.profile,
                    **render_params,
                )
            timings.append(("format", round(t.elapsed * 1000, 2)))

            if OptionalHeader.server_timing in self.optional_headers:
                headers["Server-Timing"] = ", ".join(
                    [f"{name};dur={time}" for (name, time) in timings]
                )

            return Response(content, media_type=format.mediatype, headers=headers)