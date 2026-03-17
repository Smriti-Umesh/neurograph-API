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

    created_new_edge = False

    if edge is None:
        created_new_edge = True
        old_weight = 0.0
        was_active = False

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
        old_weight = edge.weight
        was_active = edge.is_active

        edge.weight = round(edge.weight + LEARNING_INCREMENT, 4)
        edge.activation_count += 1

        if not edge.is_active and edge.weight >= RESTORE_THRESHOLD:
            edge.is_active = True

    db.commit()
    db.refresh(edge)

    publish_event(
        "graph.edge.learned",
        build_edge_learned_event(
            network_id=network_id,
            edge=edge,
            old_weight=old_weight,
            was_active=was_active,
        ),
    )

    if not created_new_edge and not was_active and edge.is_active:
        publish_event(
            "graph.edge.reactivated",
            build_edge_reactivated_event(
                network_id=network_id,
                edge=edge,
                old_weight=old_weight,
                restore_threshold=RESTORE_THRESHOLD,
            ),
        )
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

    event_records = []

    for edge in active_edges:
        old_weight = edge.weight
        was_active = edge.is_active

        edge.weight = round(max(0.0, edge.weight - DECAY_AMOUNT), 4)

        archived_now = False
        if edge.weight <= ARCHIVE_THRESHOLD:
            edge.is_active = False
            archived_now = True

        event_records.append(
            {
                "edge": edge,
                "old_weight": old_weight,
                "was_active": was_active,
                "archived_now": archived_now,
            }
        )

    db.commit()

    decayed_edges = []

    for record in event_records:
        edge = record["edge"]
        db.refresh(edge)
        decayed_edges.append(edge)

        publish_event(
            "graph.edge.decayed",
            build_edge_decayed_event(
                network_id=network_id,
                edge=edge,
                old_weight=record["old_weight"],
                was_active=record["was_active"],
            ),
        )

        if record["archived_now"]:
            publish_event(
                "graph.edge.archived",
                build_edge_archived_event(
                    network_id=network_id,
                    edge=edge,
                    archive_threshold=ARCHIVE_THRESHOLD,
                ),
            )

    return {
        "message": "Decay applied successfully",
        "decayed_edges": decayed_edges,
    }

@router.post("/networks/{network_id}/query", response_model=QueryResponse)
def query_network(network_id: int, payload: QueryRequest, db: Session = Depends(get_db)):
    network = db.query(Network).filter(Network.id == network_id).first()
    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network not found"
        )

    if not payload.seed_node_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one seed node is required"
        )

    seed_nodes = db.query(Node).filter(Node.id.in_(payload.seed_node_ids)).all()
    found_seed_ids = {node.id for node in seed_nodes}

    missing_seed_ids = [node_id for node_id in payload.seed_node_ids if node_id not in found_seed_ids]
    if missing_seed_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seed node(s) not found: {missing_seed_ids}"
        )

    for node in seed_nodes:
        if node.network_id != network_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All seed nodes must belong to the specified network"
            )

    results_map = {}
    queue = []

    for seed_node_id in payload.seed_node_ids:
        queue.append((seed_node_id, 1.0, [seed_node_id], 0))
        results_map[seed_node_id] = {
            "score": 1.0,
            "path": [seed_node_id],
        }

    while queue:
        current_node_id, current_score, current_path, hops = queue.pop(0)

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

            if next_score < payload.min_score:
                continue

            if next_node_id in current_path:
                continue

            next_path = current_path + [next_node_id]

            existing_result = results_map.get(next_node_id)
            if existing_result is None or next_score > existing_result["score"]:
                results_map[next_node_id] = {
                    "score": next_score,
                    "path": next_path,
                }
                queue.append((next_node_id, next_score, next_path, hops + 1))

    results = []
    seed_id_set = set(payload.seed_node_ids)

    for node_id, data in results_map.items():
        if node_id in seed_id_set:
            continue

        results.append(
            {
                "node_id": node_id,
                "score": data["score"],
                "path": data["path"],
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "message": "Query completed successfully",
        "results": results,
    }