import planetary_computer as pc
import rasterio
from titiler.core import utils as titiler_utils

def test_rasterio_lerc_decompression() -> None:
    # Read a LERC file from Planetary Computer
    url = "https://usgslidareuwest.blob.core.windows.net/usgs-3dep-cogs/usgs-cogs/USGS_LPC_VA_Fairfax_County_2018/hag/USGS_LPC_VA_Fairfax_County_2018-hag-2m-3-1.tif"
    signed_url = pc.sign(url)
    with rasterio.open(signed_url) as src:
        compression = src.profile.get('compress')
        assert compression == 'lerc_zstd'