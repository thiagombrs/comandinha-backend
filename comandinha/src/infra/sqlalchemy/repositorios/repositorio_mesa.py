
from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select, delete as sa_delete
from fastapi import HTTPException, status
from typing import Optional, List, Tuple
from src.infra.sqlalchemy.models.mesa import Mesa
from src.infra.sqlalchemy.models.pedido import Pedido as ModelPedido

# 1=disponivel, 2=em_uso, 3=expirada, 4=desativada
STATUS_MAP: dict[int, str] = {
    1: "disponivel",
    2: "em_uso",
    3: "expirada",
    4: "desativada",
}

class MesaRepositorio:
    def __init__(self, db: Session):
        self.db = db

    # ---------- helpers ----------
    @staticmethod
    def _status_from_mesa(m: Mesa) -> Tuple[str, int]:
        """
        1 - disponivel   (ativo=True e sem pedidos abertos)
        2 - em_uso       (ativo=True e com pedidos não concluídos)
        4 - desativada   (ativo=False)
        """
        if m.ativo is False:
            return "desativada", 4
        # se houver pedidos ativos, considere em_uso
        tem_ativos = any(p.status != "concluido" for p in m.pedidos)
        sid = 2 if tem_ativos else (m.status_id or 1)
        return STATUS_MAP.get(sid, "disponivel"), sid

    def _tem_pedidos_ativos(self, mesa_id: int) -> bool:
        return (
            self.db.query(ModelPedido)
            .filter(ModelPedido.mesa_id == mesa_id, ModelPedido.status != "concluido")
            .limit(1).count() > 0
        )

    # ---------- CRUD ----------
    def listar_mesas(self) -> List[Mesa]:
        stmt = select(Mesa)
        return self.db.scalars(stmt).all()

    def get_mesa_por_uuid(self, mesa_uuid: str) -> Optional[Mesa]:
        stmt = select(Mesa).where(Mesa.uuid == mesa_uuid)
        return self.db.scalars(stmt).first()

    def get_mesa_por_id(self, mesa_id: int) -> Optional[Mesa]:
        return self.db.get(Mesa, mesa_id)

    def criar_mesa(self, nome: str) -> Mesa:
        mesa = Mesa(nome=nome, ativo=True)  # nasce ativa, sem token
        self.db.add(mesa)
        self.db.commit()
        self.db.refresh(mesa)
        return mesa

    def excluir_mesa(self, mesa_id: int):
        m = self.get_mesa_por_id(mesa_id)
        if not m:
            raise HTTPException(status_code=404, detail="Mesa não encontrada")
        self.db.delete(m)
        self.db.commit()

    # ---------- atualização de status ----------
    def _set_status(self, mesa: Mesa, status_id: int) -> Mesa:
        if status_id not in STATUS_MAP:
            raise HTTPException(status_code=400, detail="status_id inválido (use 1..4)")
        mesa.status_id = status_id            # <— agora grava em status_id
        mesa.ativo = (status_id != 4)         # manter compatibilidade
        self.db.add(mesa)
        self.db.commit()
        self.db.refresh(mesa)
        return mesa

    def alterar_status(self, mesa_id: int, status_id: int) -> Mesa:
        if status_id not in (1, 4):
            raise HTTPException(status_code=400, detail="status_id inválido (use 1 ou 4)")
        mesa = self.get_mesa_por_id(mesa_id)
        if not mesa:
            raise HTTPException(status_code=404, detail="Mesa não encontrada")
        if self._tem_pedidos_ativos(mesa_id):
            raise HTTPException(status_code=400, detail="Mesa possui pedidos ativos")
        return self._set_status(mesa, status_id)

    def limpar_sessao_voltar_disponivel(self, mesa_id: int) -> Mesa:
        mesa = self.get_mesa_por_id(mesa_id)
        if not mesa:
            raise HTTPException(status_code=404, detail="Mesa não encontrada")
        return self._set_status(mesa, 1)
