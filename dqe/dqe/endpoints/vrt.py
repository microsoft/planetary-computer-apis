from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException, Response
from stac_pydantic import ItemCollection
from stac_vrt import build_vrt


@dataclass
class VRTFactory:
    """VRT Endpoint Factory"""

    router: APIRouter = field(default_factory=APIRouter)

    def __post_init__(self) -> None:
        """Post Init: register route and configure specific options."""
        self.register_routes()

    def register_routes(self) -> None:
        @self.router.get("/")
        async def vrt(
            stac_items: ItemCollection,
            data_type: str = "Byte",
            block_width: int = 512,
            block_height: int = 512,
        ) -> Response:
            """
            Create a GDAL VRT from a STAC ItemCollection. The items should have
            the fields from the `proj` STAC extension:

            * `proj:epsg`
            * `proj:shape`
            * `proj:transform`
            * `proj:bbox`

            See https://gdal.org/drivers/raster/vrt.html for more on VRTs.
            """
            try:
                vrt = build_vrt(
                    stac_items.to_dict()["features"],
                    data_type=data_type,
                    block_width=block_width,
                    block_height=block_height,
                )
            except (ValueError, KeyError) as e:
                raise HTTPException(status_code=400, detail=str(e))

            return Response(content=vrt, media_type="application/xml")


vrt_factory = VRTFactory()
