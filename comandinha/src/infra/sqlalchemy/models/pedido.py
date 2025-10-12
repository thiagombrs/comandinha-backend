# src/infra/sqlalchemy/models/pedido.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, CheckConstraint
from sqlalchemy.orm import relationship, validates
from datetime import datetime, timezone
from src.infra.sqlalchemy.config.database import Base

from src.common.tz import now_sp, TZ

STATUS_TEXT_TO_ID = {
    "pendente": 1,
    "em preparo": 2,
    "entregue": 3,
    "concluido": 4,
}
STATUS_ID_TO_TEXT = {v: k for k, v in STATUS_TEXT_TO_ID.items()}

class Pedido(Base):
    __tablename__ = "pedido"
    __table_args__ = (
        CheckConstraint("status_id IN (1,2,3,4)", name="ck_pedido_status_id_range"),
    )

    id = Column(Integer, primary_key=True)
    mesa_id = Column(Integer, ForeignKey("mesa.id"), nullable=False)

    timestamp = Column(DateTime(timezone=True), default=now_sp, nullable=False)
    atualizado_em = Column(DateTime(timezone=True), nullable=True)
    estimativa_entrega = Column(DateTime(timezone=True), nullable=True)


    status_id = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="pendente")

    observacoes_gerais = Column(String, nullable=True)
    valor_total = Column(Float, nullable=True)

    mesa = relationship("Mesa", back_populates="pedidos")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")

    @validates("status_id")
    def _sync_status_text_on_id(self, key, sid):
        sid = int(sid) if sid is not None else 1
        self.status = STATUS_ID_TO_TEXT.get(sid, "pendente")
        return sid

    # ⚠️ Não tenha validador de 'status' que seta 'status_id' (evita recursão)
