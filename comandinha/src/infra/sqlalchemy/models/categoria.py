from sqlalchemy import Column, Integer, String, Boolean
from src.infra.sqlalchemy.config.database import Base
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, JSON
)
from sqlalchemy.orm import relationship

class Categoria(Base):
    __tablename__ = "categoria"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String, nullable=True)
    imagem_url = Column(String, nullable=True)
    ordem = Column(Integer, nullable=True)
    ativa = Column(Boolean, default=True)

    produtos = relationship("Produto", back_populates="categoria")
