from pydantic import BaseModel


class ProxyCreate(BaseModel):
    address: str


class ProxyResponse(BaseModel):
    id: int
    address: str
    enabled: bool
    failures: int
