from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Edge(Base):
    __tablename__ = "edges"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    network_id: Mapped[int] = mapped_column(ForeignKey("networks.id"), nullable=False)
    source_node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"), nullable=False)
    target_node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False)