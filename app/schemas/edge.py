from pydantic import BaseModel


class EdgeCreate(BaseModel):
    source_node_id: int
    target_node_id: int
    relationship_type: str


class EdgeUpdate(BaseModel):
    relationship_type: str


class EdgeResponse(BaseModel):
    id: int
    network_id: int
    source_node_id: int
    target_node_id: int
    relationship_type: str

    model_config = {"from_attributes": True}