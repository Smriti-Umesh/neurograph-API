from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.events.builders import (
    build_edge_archived_event,
    build_edge_decayed_event,
    build_edge_learned_event,
    build_edge_reactivated_event,
)
from app.events.publisher import publish_event
from app.models.edge import Edge
from app.models.network import Network
from app.models.node import Node
from app.schemas.edge import (
    EdgeCreate,
    EdgeUpdate,
    EdgeResponse,
    LearnRequest,
    LearnResponse,
    DecayResponse,
    QueryRequest,
    QueryResponse,
)
from app.services.graph_service import apply_learning, apply_decay, query_graph

"""
Edges Router

This module handles:
- Edge CRUD operations
- Learning (Hebbian updates)
- Decay + archiving
- Graph querying via spreading activation

Edges represent relationships between nodes and are dynamically updated
based on usage (learning/decay).
"""


router = APIRouter(tags=["edges"])
# Learning parameters (control how the graph evolves over time)
LEARNING_INCREMENT = 0.1
INITIAL_WEIGHT = 1.0

# Decay over time and memory behaviour
DECAY_AMOUNT = 0.2
ARCHIVE_THRESHOLD = 0.3

# Restoration behaviour
RESTORE_THRESHOLD = 0.5
PROPAGATION_DECAY = 0.5


@router.post("/networks/{network_id}/edges", response_model=EdgeResponse, status_code=status.HTTP_201_CREATED)
def create_edge(network_id: int, payload: EdgeCreate, db: Session = Depends(get_db)):
    network = db.query(Network).filter(Network.id == network_id).first()
    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network not found"
        )

    source_node = db.query(Node).filter(Node.id == payload.source_node_id).first()
    if source_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source node not found"
        )

    target_node = db.query(Node).filter(Node.id == payload.target_node_id).first()
    if target_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target node not found"
        )
     # Ensure both nodes belong to the same network
    if source_node.network_id != network_id or target_node.network_id != network_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both nodes must belong to the specified network"
        )
     # Create a new edge with initial "active memory" state
    edge = Edge(
        network_id=network_id,
        source_node_id=payload.source_node_id,
        target_node_id=payload.target_node_id,
        relationship_type=payload.relationship_type,
        weight=1.0,
        is_active=True,
        activation_count=0,
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)

    return edge


@router.post("/networks/{network_id}/learn", response_model=LearnResponse)
def learn_edge(network_id: int, payload: LearnRequest, db: Session = Depends(get_db)):
    # Applies Hebbian-style updates (strengthens co-activated nodes)
    return apply_learning(
        db=db,
        network_id=network_id,
        source_node_id=payload.source_node_id,
        target_node_id=payload.target_node_id,
        relationship_type=payload.relationship_type,
    )
@router.get("/networks/{network_id}/edges", response_model=list[EdgeResponse])
def list_edges(network_id: int, db: Session = Depends(get_db)):
    network = db.query(Network).filter(Network.id == network_id).first()
    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network not found"
        )

    edges = db.query(Edge).filter(Edge.network_id == network_id).all()
    return edges


@router.get("/edges/{edge_id}", response_model=EdgeResponse)
def get_edge(edge_id: int, db: Session = Depends(get_db)):
    edge = db.query(Edge).filter(Edge.id == edge_id).first()

    if edge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edge not found"
        )

    return edge


@router.patch("/edges/{edge_id}", response_model=EdgeResponse)
def update_edge(edge_id: int, payload: EdgeUpdate, db: Session = Depends(get_db)):
    edge = db.query(Edge).filter(Edge.id == edge_id).first()

    if edge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edge not found"
        )

    edge.relationship_type = payload.relationship_type
    db.commit()
    db.refresh(edge)

    return edge


@router.delete("/edges/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_edge(edge_id: int, db: Session = Depends(get_db)):
    edge = db.query(Edge).filter(Edge.id == edge_id).first()

    if edge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edge not found"
        )

    db.delete(edge)
    db.commit()

    return None


@router.post("/networks/{network_id}/decay", response_model=DecayResponse)
def decay_edges(network_id: int, db: Session = Depends(get_db)):
    # Weak edges may be archived (soft deletion behaviour)
    return apply_decay(db=db, network_id=network_id)


@router.post("/networks/{network_id}/query", response_model=QueryResponse)
def query_network(network_id: int, payload: QueryRequest, db: Session = Depends(get_db)):
    # Performs spreading activation starting from seed nodes
    # Traverses only active edges
    # Returns ranked nodes with explanation paths
    return query_graph(
        db=db,
        network_id=network_id,
        seed_node_ids=payload.seed_node_ids,
        max_hops=payload.max_hops,
        min_score=payload.min_score,
    )