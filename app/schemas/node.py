from pydantic import BaseModel


class NodeCreate(BaseModel):
    label: str
    node_type: str


class NodeUpdate(BaseModel):
    label: str
    node_type: str


class NodeResponse(BaseModel):
    id: int
    network_id: int
    label: str
    node_type: str

    model_config = {"from_attributes": True}