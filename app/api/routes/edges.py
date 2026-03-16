from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.network import Network
from app.models.node import Node
from app.models.edge import Edge
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

router = APIRouter(tags=["edges"])

LEARNING_INCREMENT = 0.1
INITIAL_WEIGHT = 1.0
DECAY_AMOUNT = 0.2
ARCHIVE_THRESHOLD = 0.3
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

    if source_node.network_id != network_id or target_node.network_id != network_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both nodes must belong to the specified network"
        )

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

    if source_node.network_id != network_id or target_node.network_id != network_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both nodes must belong to the specified network"
        )

    edge = (
        db.query(Edge)
        .filter(
            Edge.network_id == network_id,
            Edge.source_node_id == payload.source_node_id,
            Edge.target_node_id == payload.target_node_id,
        )
        .first()
    )

    if edge is None:
        edge = Edge(
            network_id=network_id,
            source_node_id=payload.source_node_id,
            target_node_id=payload.target_node_id,
            relationship_type=payload.relationship_type,
            weight=INITIAL_WEIGHT,
            is_active=True,
            activation_count=1,
        )
        db.add(edge)
    else:
        edge.weight += LEARNING_INCREMENT
        edge.activation_count += 1

        if not edge.is_active and edge.weight >= RESTORE_THRESHOLD:
            edge.is_active = True

    db.commit()
    db.refresh(edge)

    return {
        "message": "Learning applied successfully",
        "edge": edge,
    }


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
    network = db.query(Network).filter(Network.id == network_id).first()
    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network not found"
        )

    active_edges = (
        db.query(Edge)
        .filter(
            Edge.network_id == network_id,
            Edge.is_active.is_(True),
        )
        .all()
    )

    for edge in active_edges:
        edge.weight = max(0.0, edge.weight - DECAY_AMOUNT)

        if edge.weight <= ARCHIVE_THRESHOLD:
            edge.is_active = False

    db.commit()

    for edge in active_edges:
        db.refresh(edge)

    return {
        "message": "Decay applied successfully",
        "decayed_edges": active_edges,
    }

@router.post("/networks/{network_id}/query", response_model=QueryResponse)
def query_network(network_id: int, payload: QueryRequest, db: Session = Depends(get_db)):
    network = db.query(Network).filter(Network.id == network_id).first()
    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network not found"
        )

    seed_node = db.query(Node).filter(Node.id == payload.seed_node_id).first()
    if seed_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seed node not found"
        )

    if seed_node.network_id != network_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seed node must belong to the specified network"
        )

    results = []
    queue = [(payload.seed_node_id, 1.0, [payload.seed_node_id], 0)]
    best_scores = {payload.seed_node_id: 1.0}

    while queue:
        current_node_id, current_score, path, hops = queue.pop(0)

        if hops >= payload.max_hops:
            continue

        outgoing_edges = (
            db.query(Edge)
            .filter(
                Edge.network_id == network_id,
                Edge.source_node_id == current_node_id,
                Edge.is_active.is_(True),
            )
            .all()
        )

        for edge in outgoing_edges:
            next_node_id = edge.target_node_id
            next_score = current_score * edge.weight * PROPAGATION_DECAY
            next_path = path + [next_node_id]

            if next_node_id not in best_scores or next_score > best_scores[next_node_id]:
                best_scores[next_node_id] = next_score
                queue.append((next_node_id, next_score, next_path, hops + 1))

    for node_id, score in best_scores.items():
        if node_id == payload.seed_node_id:
            continue

        path_queue = [(payload.seed_node_id, [payload.seed_node_id], 0, 1.0)]
        best_path = None
        best_path_score = -1.0

        while path_queue:
            current_node_id, current_path, hops, current_path_score = path_queue.pop(0)

            if hops >= payload.max_hops:
                continue

            outgoing_edges = (
                db.query(Edge)
                .filter(
                    Edge.network_id == network_id,
                    Edge.source_node_id == current_node_id,
                    Edge.is_active.is_(True),
                )
                .all()
            )

            for edge in outgoing_edges:
                candidate_node_id = edge.target_node_id
                candidate_score = current_path_score * edge.weight * PROPAGATION_DECAY
                candidate_path = current_path + [candidate_node_id]

                if candidate_node_id == node_id and candidate_score > best_path_score:
                    best_path = candidate_path
                    best_path_score = candidate_score

                if candidate_node_id not in current_path:
                    path_queue.append((candidate_node_id, candidate_path, hops + 1, candidate_score))

        results.append(
            {
                "node_id": node_id,
                "score": score,
                "path": best_path or [payload.seed_node_id, node_id],
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "message": "Query completed successfully",
        "results": results,
    }