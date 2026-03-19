from sqlalchemy import Column, ForeignKey, Integer, String

from app.core.db import Base


class Network(Base):
    __tablename__ = "networks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)