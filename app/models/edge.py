from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from  app.core.db import Base


class Edge(Base):
    __tablename__ = "edges"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    network_id: Mapped[int] = mapped_column(ForeignKey("networks.id"), nullable=False)
    source_node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"), nullable=False)
    target_node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # strength of the connectionwith default value of 1.0, can be used for weighted spreading activation
    weight: Mapped[float] = mapped_column(nullable=False, default=1.0)
    
    # This tells us whether the edge is currently active. 
    # In spreading activation, we might want to temporarily deactivate 
    # certain edges to prevent cycles or to model inhibition.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # counts how many times the edge has been strengthened.
    activation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)