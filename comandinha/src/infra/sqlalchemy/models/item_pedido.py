from sqlalchemy import (
    Column, Integer, String, ForeignKey, Float, JSON
)
from sqlalchemy.orm import relationship
from src.infra.sqlalchemy.config.database import Base

class ItemPedido(Base):
    __tablename__ = "item_pedido"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedido.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produto.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    observacoes = Column(String, nullable=True)
    subtotal = Column(Float, nullable=False)

    produto = relationship("Produto")  # puxa nome, preço, etc.
    pedido = relationship("Pedido", back_populates="itens")
