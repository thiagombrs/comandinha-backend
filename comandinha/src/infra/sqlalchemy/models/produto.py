from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from src.infra.sqlalchemy.config.database import Base

class Produto(Base):
    __tablename__ = "produto"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String, nullable=True)
    preco = Column(Float, nullable=False)
    imagem_url = Column(String, nullable=True)
    popular = Column(Boolean, default=False)
    tempo_preparo_minutos = Column(Integer, nullable=True)

    # campos novos
    restricoes = Column(JSON, nullable=True)    # ex: ["vegetariano","vegano"]
    adicionais = Column(JSON, nullable=True)    # ex: [{"id":"a1","nome":"Queijo","preco":5.0}]

    categoria_id = Column(
        Integer,
        ForeignKey("categoria.id", name="fk_produto_categoria"),
        nullable=False
    )
    # aqui deve ser 'produtos', pois em Categoria você tem:
    #   produtos = relationship("Produto", back_populates="categoria")
    categoria = relationship("Categoria", back_populates="produtos")
