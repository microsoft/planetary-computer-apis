from pydantic import BaseModel


class PCAssetPath(BaseModel):
    collection: str
    item: str
    asset: str


class AzMapsToken(BaseModel):
    token: str
    expires_on: int
