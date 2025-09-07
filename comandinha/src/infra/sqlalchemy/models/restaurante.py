from sqlalchemy import Column, Integer, String, DateTime, func
from src.infra.sqlalchemy.config.database import Base

class Restaurante(Base):
    __tablename__ = "restaurantes"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    senha_hash = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
