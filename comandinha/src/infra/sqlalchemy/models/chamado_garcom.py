from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from src.infra.sqlalchemy.config.database import Base

# Códigos:
# Motivo: 1=assistencia, 2=fechar_conta, 3=urgente
# Status: 1=pendente,   2=atendida,     3=cancelada

class ChamadoGarcom(Base):
    __tablename__ = "chamadas_garcom"

    id = Column(Integer, primary_key=True, index=True)                 # AUTOINCREMENT implícito
    mesa_uuid = Column(String(36), ForeignKey("mesa.uuid"), index=True, nullable=False)

    motivo = Column(Integer, nullable=False)                           # <-- agora INTEGER
    detalhes = Column(String, nullable=True)

    status = Column(Integer, nullable=False, default=1)                # <-- agora INTEGER (1=pendente)
    criado_em = Column(DateTime, nullable=False, default=lambda: datetime.now())
    atendido_em = Column(DateTime, nullable=True)
    cancelado_em = Column(DateTime, nullable=True)

    atendido_por = Column(String(64), nullable=True)                   # id/uuid do admin (sem FK por ora)
    mesa = relationship("Mesa", lazy="joined")

Index("ix_chamadas_status", ChamadoGarcom.status)
Index("ix_chamadas_mesa_status", ChamadoGarcom.mesa_uuid, ChamadoGarcom.status)
