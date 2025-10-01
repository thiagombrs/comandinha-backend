# src/infra/sqlalchemy/repositorios/repositorio_chamado.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Union

from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from src.infra.sqlalchemy.models.chamado_garcom import ChamadoGarcom

# ------------------ Mapas de códigos <-> texto ------------------
MOTIVO_CODE_TO_TEXT: Dict[int, str] = {1: "assistencia", 2: "fechar_conta", 3: "urgente"}
STATUS_CODE_TO_TEXT: Dict[int, str] = {1: "pendente", 2: "atendida", 3: "cancelada"}

MOTIVO_TEXT_TO_CODE: Dict[str, int] = {v: k for k, v in MOTIVO_CODE_TO_TEXT.items()}
STATUS_TEXT_TO_CODE: Dict[str, int] = {v: k for k, v in STATUS_CODE_TO_TEXT.items()}

# Códigos de status usados no banco
STATUS_PENDENTE  = 1
STATUS_ATENDIDA  = 2
STATUS_CANCELADA = 3

# Códigos de motivo
MOTIVO_ASSISTENCIA  = 1
MOTIVO_FECHAR_CONTA = 2
MOTIVO_URGENTE      = 3

# Conjunto de motivos que entram no cooldown entre si (assistência <-> urgente)
PAIR_COOLDOWN = {MOTIVO_ASSISTENCIA, MOTIVO_URGENTE}

COOLDOWN = timedelta(minutes=3)

def _now() -> datetime:
    return datetime.now()  # naive, compatível com SQLite

def _status_txt(code: int) -> str:
    return STATUS_CODE_TO_TEXT.get(code, "pendente")

def _motivo_txt(code: int) -> str:
    return MOTIVO_CODE_TO_TEXT.get(code, "assistencia")

def _status_code(value: Union[int, str]) -> int:
    if isinstance(value, int):
        if value not in STATUS_CODE_TO_TEXT:
            raise ValueError("Status inválido. Use 1=pendente, 2=atendida, 3=cancelada")
        return value
    v = (value or "").strip().lower()
    if v not in STATUS_TEXT_TO_CODE:
        raise ValueError("Status inválido. Use pendente|atendida|cancelada")
    return STATUS_TEXT_TO_CODE[v]

def _motivo_code(value: Union[int, str]) -> int:
    if isinstance(value, int):
        if value not in MOTIVO_CODE_TO_TEXT:
            raise ValueError("Motivo inválido. Use 1=assistencia, 2=fechar_conta, 3=urgente")
        return value
    v = (value or "").strip().lower()
    if v not in MOTIVO_TEXT_TO_CODE:
        raise ValueError("Motivo inválido. Use assistencia|fechar_conta|urgente")
    return MOTIVO_TEXT_TO_CODE[v]


class RepositorioChamado:
    """
    Regras:
      - NÃO permitir dois PENDENTES do MESMO motivo para a MESMA mesa.
      - Cooldown (3min) ENTRE assistencia(1) <-> urgente(3), nos dois sentidos,
        MESMO se o anterior ainda estiver pendente.
      - Sem cooldown envolvendo fechar_conta(2).
      - motivo/status são INTEGER no banco; resposta sai como string.
    """
    def __init__(self, db: Session):
        self.db = db

    # ------------------------ MESA ------------------------
    def criar(self, mesa_uuid: str, motivo: Union[int, str], detalhes: Optional[str]) -> ChamadoGarcom:
        motivo_code = _motivo_code(motivo)

        # (1) BLOQUEAR DUPLICIDADE PENDENTE DO MESMO MOTIVO
        pendente_mesmo_motivo = (
            self.db.query(ChamadoGarcom)
            .filter(
                ChamadoGarcom.mesa_uuid == mesa_uuid,
                ChamadoGarcom.motivo == motivo_code,
                ChamadoGarcom.status == STATUS_PENDENTE,
            )
            .first()
        )
        if pendente_mesmo_motivo:
            raise ValueError("Já existe um chamado pendente deste mesmo motivo para esta mesa.")

        # (2) COOLDOWN 3min ENTRE ASSISTÊNCIA <-> URGENTE, MESMO SE O ANTERIOR ESTIVER PENDENTE
        #     Buscamos o ÚLTIMO chamado (pendente OU concluído) cujo motivo esteja no par {1,3}.
        #     Se for do OUTRO motivo e t_ref < 3 min, bloqueia.
        if motivo_code in PAIR_COOLDOWN:
            ultimo_par = (
                self.db.query(ChamadoGarcom)
                .filter(
                    ChamadoGarcom.mesa_uuid == mesa_uuid,
                    ChamadoGarcom.motivo.in_(PAIR_COOLDOWN),
                )
                .order_by(
                    func.coalesce(
                        ChamadoGarcom.atendido_em,
                        ChamadoGarcom.cancelado_em,
                        ChamadoGarcom.criado_em
                    ).desc()
                )
                .first()
            )
            if ultimo_par and ultimo_par.motivo in PAIR_COOLDOWN and ultimo_par.motivo != motivo_code:
                t_ref = ultimo_par.atendido_em or ultimo_par.cancelado_em or ultimo_par.criado_em
                if t_ref and (_now() - t_ref) < COOLDOWN:
                    raise TimeoutError("Aguarde 3 minutos para alternar entre assistência e urgência.")

        # (3) SE CHEGOU AQUI, PODE CRIAR
        novo = ChamadoGarcom(
            mesa_uuid=mesa_uuid,
            motivo=motivo_code,                           # INTEGER
            detalhes=(detalhes or "").strip() or None,
            status=STATUS_PENDENTE,                       # INTEGER (1)
        )
        self.db.add(novo)
        self.db.commit()
        self.db.refresh(novo)
        return novo

    def cancelar_da_mesa(self, chamado_id: int, mesa_uuid: str) -> ChamadoGarcom:
        ch = self.db.get(ChamadoGarcom, chamado_id)
        if not ch or ch.mesa_uuid != mesa_uuid:
            raise LookupError("Chamado não encontrado para esta mesa.")
        if ch.status != STATUS_PENDENTE:
            raise ValueError("Só é possível cancelar chamados pendentes.")
        ch.status = STATUS_CANCELADA
        ch.cancelado_em = _now()
        self.db.commit()
        self.db.refresh(ch)
        return ch

    def historico_da_mesa(self, mesa_uuid: str, limite: int = 50) -> List[ChamadoGarcom]:
        return (
            self.db.query(ChamadoGarcom)
            .filter(ChamadoGarcom.mesa_uuid == mesa_uuid)
            .order_by(desc(ChamadoGarcom.criado_em))
            .limit(limite)
            .all()
        )

    # ----------------------- ADMIN ------------------------
    def listar_pendentes(self) -> List[ChamadoGarcom]:
        return (
            self.db.query(ChamadoGarcom)
            .filter(ChamadoGarcom.status == STATUS_PENDENTE)
            .order_by(ChamadoGarcom.criado_em.asc())
            .all()
        )

    def atender(self, chamado_id: int, admin_ident: Union[str, int]) -> ChamadoGarcom:
        ch = self.db.get(ChamadoGarcom, chamado_id)
        if not ch:
            raise LookupError("Chamado não encontrado.")
        if ch.status != STATUS_PENDENTE:
            raise ValueError("Chamado não está pendente.")
        ch.status = STATUS_ATENDIDA
        ch.atendido_em = _now()
        ch.atendido_por = str(admin_ident)
        self.db.commit()
        self.db.refresh(ch)
        return ch

    def historico(
        self,
        desde: Optional[datetime] = None,
        status: Optional[Union[int, str]] = None,
        limite: int = 100,
        mesa_uuid: Optional[str] = None,
    ) -> List[ChamadoGarcom]:
        q = self.db.query(ChamadoGarcom)
        if mesa_uuid:
            q = q.filter(ChamadoGarcom.mesa_uuid == mesa_uuid)
        if desde:
            q = q.filter(ChamadoGarcom.criado_em >= desde)
        if status is not None:
            q = q.filter(ChamadoGarcom.status == _status_code(status))
        return q.order_by(desc(ChamadoGarcom.criado_em)).limit(limite).all()

    # ------------------- Serialização --------------------
    @staticmethod
    def to_response_dict(ch: ChamadoGarcom) -> dict:
        """Resposta com strings + (opcional) códigos."""
        return {
            "id": ch.id,
            "mesa_uuid": ch.mesa_uuid,
            "motivo": _motivo_txt(ch.motivo),   # string
            "status": _status_txt(ch.status),   # string
            "motivo_code": ch.motivo,           # opcional
            "status_code": ch.status,           # opcional
            "detalhes": ch.detalhes,
            "criado_em": ch.criado_em,
            "atendido_em": ch.atendido_em,
            "cancelado_em": ch.cancelado_em,
            "atendido_por": ch.atendido_por,
        }
