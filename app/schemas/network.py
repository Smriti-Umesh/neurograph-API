from pydantic import BaseModel


class NetworkCreate(BaseModel):
    name: str


class NetworkUpdate(BaseModel):
    name: str


class NetworkResponse(BaseModel):
    id: int
    name: str
    owner_id: int

    model_config = {"from_attributes": True}