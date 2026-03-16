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
    weight: float
    is_active: bool
    activation_count: int

    model_config = {"from_attributes": True}

# the body sent to the learning endpoint.
class LearnRequest(BaseModel):
    source_node_id: int
    target_node_id: int
    relationship_type: str = "related_to"


class LearnResponse(BaseModel):
    message: str
    edge: EdgeResponse