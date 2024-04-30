from fastapi import APIRouter

from pccommon.credential import PcDefaultAzureCredential
from pctiler.models import AzMapsToken

tokenProvider = PcDefaultAzureCredential()
configuration_router = APIRouter()


@configuration_router.get("/map/token", response_model=AzMapsToken)
def get_azmaps_token() -> AzMapsToken:
    """
    Fetch a token for the Azure Maps API service based on the current
    service identity. This token is used for the Explorer to authenticate
    with the Azure Maps API service.
    """
    accessToken = tokenProvider.get_token("https://atlas.microsoft.com/.default")
    return AzMapsToken(token=accessToken.token, expires_on=accessToken.expires_on)
