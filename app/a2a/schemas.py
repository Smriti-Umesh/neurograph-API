# app/a2a/schemas.py

from pydantic import BaseModel
from typing import Any, Literal, Optional


class A2AMessage(BaseModel):
    message_id: str
    message_type: str
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    sender: Optional[str] = None
    payload: dict[str, Any]


class LearnRequestPayload(BaseModel):
    network_id: int
    source_node_id: int
    target_node_id: int
    relationship_type: str = "related_to"


class QueryRequestPayload(BaseModel):
    network_id: int
    seed_node_ids: list[int]
    max_hops: int = 4
    min_score: float = 0.05


class DecayRequestPayload(BaseModel):
    network_id: int


class ErrorPayload(BaseModel):
    error: str
    detail: str