from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.infra.sqlalchemy.config.database import Base

class ChamadoGarcom(Base):
    __tablename__ = 'chamados_garcom'

    id = Column(Integer, primary_key=True, index=True)
    mesa_id = Column(Integer, ForeignKey('mesa.id', name='fk_chamado_mesa'), nullable=False)
    motivo = Column(String, nullable=False)
    detalhes = Column(String, nullable=True)
    status = Column(String, nullable=False, default="enviado")
    timestamp = Column(DateTime, nullable=False)

    mesa = relationship("Mesa", back_populates="chamados")
