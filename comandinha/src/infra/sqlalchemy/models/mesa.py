# src/infra/sqlalchemy/models/mesa.py

from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from src.infra.sqlalchemy.config.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Mesa(Base):
    __tablename__ = 'mesa'

    id         = Column(Integer, primary_key=True, index=True)
    uuid       = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    nome       = Column(String, nullable=False)
    ativo      = Column(Boolean, default=False)
    status_id  = Column(Integer, nullable=False, default=1)  # <— renomeada

    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    pedidos   = relationship("Pedido", back_populates="mesa")
    chamados  = relationship("ChamadoGarcom", back_populates="mesa", cascade="all, delete-orphan")
