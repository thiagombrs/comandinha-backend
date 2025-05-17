from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Float, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from src.infra.sqlalchemy.config.database import Base

class Pedido(Base):
    __tablename__ = "pedido"

    id = Column(Integer, primary_key=True, index=True)
    mesa_id = Column(Integer, ForeignKey("mesa.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, nullable=False)
    observacoes_gerais = Column(String, nullable=True)
    valor_total = Column(Float, nullable=True)
    estimativa_entrega = Column(DateTime, nullable=True)
    atualizado_em = Column(DateTime, nullable=True)

    mesa_id = Column(Integer, ForeignKey('mesa.id'), nullable=False)
    mesa = relationship("Mesa", back_populates="pedidos")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
