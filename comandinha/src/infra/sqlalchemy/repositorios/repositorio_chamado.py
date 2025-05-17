# src/infra/sqlalchemy/repositorios/repositorio_chamado.py
from __future__ import annotations
from sqlalchemy.orm import Session
from src.schemas.chamado import ChamadoCreateRequest
from datetime import datetime
from src.infra.sqlalchemy.models.chamado_garcom import ChamadoGarcom

class RepositorioChamado:
    def __init__(self, db: Session):
        self.db = db

    def criar_chamado(self, mesa_id: int, req: ChamadoCreateRequest) -> ChamadoGarcom:
        now = datetime.utcnow()
        chamado = ChamadoGarcom(
            mesa_id=mesa_id,
            motivo=req.motivo,
            detalhes=req.detalhes,
            status='enviado',
            timestamp=now
        )
        self.db.add(chamado)
        self.db.commit()
        self.db.refresh(chamado)
        return chamado

    def get_chamado(self, mesa_id: int, chamado_id: int) -> ChamadoGarcom | None:
        return (
            self.db.query(ChamadoGarcom)
            .filter_by(id=chamado_id, mesa_id=mesa_id)
            .first()
        )
