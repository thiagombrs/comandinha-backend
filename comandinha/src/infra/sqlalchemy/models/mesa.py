# src/infra/sqlalchemy/models/mesa.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from src.infra.sqlalchemy.config.database import Base
import uuid

class Mesa(Base):
    __tablename__ = 'mesa'

    id        = Column(Integer, primary_key=True, index=True)
    uuid      = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    nome      = Column(String, nullable=False)
    token     = Column(String, unique=True, nullable=True)
    expira_em = Column(DateTime, nullable=True)
    ativo     = Column(Boolean, default=False)

    pedidos   = relationship("Pedido", back_populates="mesa")
    chamados  = relationship("ChamadoGarcom", back_populates="mesa")
