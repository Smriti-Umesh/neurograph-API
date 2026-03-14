from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.network import Network
from app.models.node import Node
from app.models.edge import Edge
from app.schemas.edge import EdgeCreate, EdgeUpdate, EdgeResponse

router = APIRouter(tags=["edges"])


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
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)

    return edge


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