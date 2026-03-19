from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.dependencies.auth import get_current_user
from app.models.network import Network
from app.models.user import User
from app.schemas.network import NetworkCreate, NetworkUpdate, NetworkResponse

router = APIRouter(prefix="/networks", tags=["networks"])

"""
Networks Router

Handles CRUD operations for user-specific networks.

Each network represents an isolated knowledge graph owned by a user.
All operations enforce ownership to ensure users can only access
their own data (basic multi-tenant security model).
"""

@router.post("/", response_model=NetworkResponse, status_code=status.HTTP_201_CREATED)
def create_network(
    payload: NetworkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    network = Network(name=payload.name, owner_id=current_user.id)
    db.add(network)
    db.commit()
    db.refresh(network)
    return network


@router.get("/", response_model=list[NetworkResponse])
def list_networks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    networks = db.query(Network).filter(Network.owner_id == current_user.id).all()
    return networks


@router.get("/{network_id}", response_model=NetworkResponse)
def get_network(
    network_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
     # ensuring users can only access their own networks
    network = (
        db.query(Network)
        .filter(Network.id == network_id, Network.owner_id == current_user.id)
        .first()
    )

    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error: Network not found",
        )

    return network


@router.patch("/{network_id}", response_model=NetworkResponse)
def update_network(
    network_id: int,
    payload: NetworkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    network = (
        db.query(Network)
        .filter(Network.id == network_id, Network.owner_id == current_user.id)
        .first()
    )

    # Either network doesn't or user is not authorised to access it 
    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error: Network not found",
        )

    network.name = payload.name
    db.commit()
    db.refresh(network)

    return network


@router.delete("/{network_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_network(
    network_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    network = (
        db.query(Network)
        .filter(Network.id == network_id, Network.owner_id == current_user.id)
        .first()
    )

    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error: Network not found",
        )
    # Permanently remove network
    db.delete(network)
    db.commit()
    return None