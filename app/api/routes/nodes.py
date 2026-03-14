from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.network import Network
from app.models.node import Node
from app.schemas.node import NodeCreate, NodeUpdate, NodeResponse

router = APIRouter(tags=["nodes"])


@router.post("/networks/{network_id}/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
def create_node(network_id: int, payload: NodeCreate, db: Session = Depends(get_db)):
    network = db.query(Network).filter(Network.id == network_id).first()

    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network not found"
        )

    node = Node(
        network_id=network_id,
        label=payload.label,
        node_type=payload.node_type
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    return node


@router.get("/networks/{network_id}/nodes", response_model=list[NodeResponse])
def list_nodes(network_id: int, db: Session = Depends(get_db)):
    network = db.query(Network).filter(Network.id == network_id).first()

    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Network not found"
        )

    nodes = db.query(Node).filter(Node.network_id == network_id).all()
    return nodes


@router.get("/nodes/{node_id}", response_model=NodeResponse)
def get_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id).first()

    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )

    return node


@router.patch("/nodes/{node_id}", response_model=NodeResponse)
def update_node(node_id: int, payload: NodeUpdate, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id).first()

    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )

    node.label = payload.label
    node.node_type = payload.node_type

    db.commit()
    db.refresh(node)

    return node


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id).first()

    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )

    db.delete(node)
    db.commit()

    return None