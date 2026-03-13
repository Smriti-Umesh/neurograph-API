from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.network import Network
from app.schemas.network import NetworkCreate, NetworkUpdate, NetworkResponse

router = APIRouter(prefix="/networks", tags=["networks"])


@router.post("/", response_model=NetworkResponse, status_code=status.HTTP_201_CREATED)
def create_network(payload: NetworkCreate, db: Session = Depends(get_db)):
    network = Network(name=payload.name)
    db.add(network)
    db.commit()
    db.refresh(network)
    return network


@router.get("/", response_model=list[NetworkResponse])
def list_networks(db: Session = Depends(get_db)):
    networks = db.query(Network).all()
    return networks


@router.get("/{network_id}", response_model=NetworkResponse)
def get_network(network_id: int, db: Session = Depends(get_db)):
    network = db.query(Network).filter(Network.id == network_id).first()

    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error: Network not found"
        )

    return network


@router.patch("/{network_id}", response_model=NetworkResponse)
def update_network(network_id: int, payload: NetworkUpdate, db: Session = Depends(get_db)):
    network = db.query(Network).filter(Network.id == network_id).first()

    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error: Network not found"
        )

    network.name = payload.name
    db.commit()
    db.refresh(network)

    return network


@router.delete("/{network_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_network(network_id: int, db: Session = Depends(get_db)):
    network = db.query(Network).filter(Network.id == network_id).first()

    if network is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error: Network not found"
        )

    db.delete(network)
    db.commit()
    return None