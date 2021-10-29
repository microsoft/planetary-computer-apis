from pydantic import BaseModel


class PCAssetPath(BaseModel):
    collection: str
    item: str
    asset: str
