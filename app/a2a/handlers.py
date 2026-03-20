

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.a2a.schemas import (
    LearnRequestPayload,
    QueryRequestPayload,
    DecayRequestPayload,
)
from app.services.graph_service import apply_learning, apply_decay, query_graph

def handle_learn_request(db: Session, payload: dict) -> dict:
    data = LearnRequestPayload(**payload)

    result = apply_learning(
        db=db,
        network_id=data.network_id,
        source_node_id=data.source_node_id,
        target_node_id=data.target_node_id,
        relationship_type=data.relationship_type,
    )
    # Transform the result into a standardized response format 
    # that includes the updated edge information
    
    return {
        "message": result["message"],
        "edge": {
            "id": result["edge"].id,
            "network_id": result["edge"].network_id,
            "source_node_id": result["edge"].source_node_id,
            "target_node_id": result["edge"].target_node_id,
            "relationship_type": result["edge"].relationship_type,
            "weight": result["edge"].weight,
            "is_active": result["edge"].is_active,
            "activation_count": result["edge"].activation_count,
        },
    }


def handle_query_request(db: Session, payload: dict) -> dict:
    data = QueryRequestPayload(**payload)

    result = query_graph(
        db=db,
        network_id=data.network_id,
        seed_node_ids=data.seed_node_ids,
        max_hops=data.max_hops,
        min_score=data.min_score,
    )

    return result

# Handler for decay requests that applies decay to edges in the specified 
# network and returns the decayed edges
def handle_decay_request(db: Session, payload: dict) -> dict:
    data = DecayRequestPayload(**payload)

    result = apply_decay(
        db=db,
        network_id=data.network_id,
    )

    return {
        "message": result["message"],
        "decayed_edges": [
            {
                "id": edge.id,
                "network_id": edge.network_id,
                "source_node_id": edge.source_node_id,
                "target_node_id": edge.target_node_id,
                "relationship_type": edge.relationship_type,
                "weight": edge.weight,
                "is_active": edge.is_active,
                "activation_count": edge.activation_count,
            }
            for edge in result["decayed_edges"]
        ],
    }

# Main dispatcher that takes in the raw message, 
# determines the type of request,
def dispatch_a2a_message(db: Session, message_type: str, payload: dict) -> dict:
    if message_type == "learn.request":
        return handle_learn_request(db, payload)

    if message_type == "query.request":
        return handle_query_request(db, payload)

    if message_type == "decay.request":
        return handle_decay_request(db, payload)

    raise ValueError(f"Unsupported message type: {message_type}")