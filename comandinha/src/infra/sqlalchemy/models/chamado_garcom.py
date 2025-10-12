from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from src.infra.sqlalchemy.config.database import Base
from src.common.tz import now_sp, TZ

TZ = ZoneInfo("America/Sao_Paulo")

# Códigos:
# Motivo: 1=assistencia, 2=fechar_conta, 3=urgente
# Status: 1=pendente,   2=atendida,     3=cancelada

class ChamadoGarcom(Base):
    __tablename__ = "chamadas_garcom"

    id = Column(Integer, primary_key=True, index=True)                 # AUTOINCREMENT implícito
    mesa_uuid = Column(String(36), ForeignKey("mesa.uuid"), index=True, nullable=False)

    motivo = Column(Integer, nullable=False)                           # <-- agora INTEGER
    detalhes = Column(String, nullable=True)

    status = Column(Integer, nullable=False, default=1)
    criado_em = Column(DateTime(timezone=True), nullable=False, default=now_sp)
    atendido_em = Column(DateTime(timezone=True), nullable=True)
    cancelado_em = Column(DateTime(timezone=True), nullable=True)


    atendido_por = Column(String(64), nullable=True)                   # id/uuid do admin (sem FK por ora)
    mesa = relationship("Mesa", lazy="joined")

Index("ix_chamadas_status", ChamadoGarcom.status)
Index("ix_chamadas_mesa_status", ChamadoGarcom.mesa_uuid, ChamadoGarcom.status)
