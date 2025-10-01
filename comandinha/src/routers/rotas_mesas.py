from fastapi import (
    APIRouter, Depends, HTTPException, status, Response,
    Path, Query, Body
)
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone

from src.schemas.mesa import (
    MesaCriacaoRequest,
    MesaCriacaoResponse,
    MesaListResponse,
    MesaFechamentoRequest,
)
from src.schemas.pedidos import PedidoResponse
from src.infra.sqlalchemy.config.database import get_db
from src.infra.sqlalchemy.repositorios.repositorio_mesa import MesaRepositorio
from src.infra.sqlalchemy.repositorios.repositorio_pedido import RepositorioPedido
from src.dependencies import get_current_admin
from src.infra.sqlalchemy.models.restaurante import Restaurante
from src.infra.sqlalchemy.models.pedido import Pedido as ModelPedido

router = APIRouter(prefix="/mesas", tags=["mesas"])

# ---------------- Helpers ----------------

STATUS_MAP = {1: "disponivel", 2: "em_uso", 3: "expirada", 4: "desativada"}

# rotas_mesas.py — substitua APENAS este helper

STATUS_MAP = {1: "disponivel", 2: "em_uso", 3: "expirada", 4: "desativada"}

def _status_from_mesa(m) -> tuple[str, int]:
    """
    Calcula e retorna (status_texto, status_id) a partir dos campos da mesa.
      - 1 = disponivel
      - 2 = em_uso
      - 3 = expirada   (se houver regra temporal, aplique aqui)
      - 4 = desativada (ativo == False)
    """
    # Se estiver inativa, força 4
    if getattr(m, "ativo", True) is False:
        sid = 4
    else:
        # lê a coluna nova; fallback 1 se vier None
        sid = getattr(m, "status_id", None) or 1

    texto = STATUS_MAP.get(sid, "disponivel")
    return texto, sid


def _tem_pedidos(db: Session, mesa_id: int) -> bool:
    return db.query(ModelPedido).filter(ModelPedido.mesa_id == mesa_id).limit(1).count() > 0

def _iso8601(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

# ---------------- Públicos ----------------

@router.get("", response_model=List[MesaListResponse], status_code=status.HTTP_200_OK)
def listar_mesas_publico(db: Session = Depends(get_db)):
    repo = MesaRepositorio(db)
    mesas = repo.listar_mesas()  # ou como você já busca
    resp = []
    for m in mesas:
        status_str, status_id = _status_from_mesa(m)
        resp.append({
            "id": m.id,
            "uuid": m.uuid,
            "nome": m.nome,
            "status": status_str,
            "status_id": status_id,
        })
    return resp



@router.get("/uuid/{mesa_uuid}", response_model=MesaListResponse)
def obter_mesa_por_uuid(mesa_uuid: str, db: Session = Depends(get_db)):
    repo = MesaRepositorio(db)
    m = repo.get_mesa_por_uuid(mesa_uuid)
    if not m:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    status_str, status_id = _status_from_mesa(m)
    return {
        "id": m.id,
        "uuid": m.uuid,
        "nome": m.nome,
        "status": status_str,
        "status_id": status_id,
    }

# ---------------- Admin ----------------

@router.post("", response_model=MesaCriacaoResponse, status_code=status.HTTP_201_CREATED)
def criar_mesa_endpoint(
    req: MesaCriacaoRequest,
    _: Restaurante = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    repo = MesaRepositorio(db)
    mesa = repo.criar_mesa(req.nome)
    status_str, status_id = _status_from_mesa(mesa)
    return MesaCriacaoResponse(id=mesa.id, uuid=mesa.uuid, nome=mesa.nome).model_copy(
        update={"status": status_str, "status_id": status_id}
    )

@router.delete("/{mesa_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_mesa_endpoint(
    mesa_id: int = Path(...),
    _: Restaurante = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    mrepo = MesaRepositorio(db)
    m = mrepo.get_mesa_por_id(mesa_id)
    if not m:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa não encontrada")
    _, status_id = _status_from_mesa(m)
    if status_id != 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Só é permitido deletar mesa 'disponivel'")
    mrepo.excluir_mesa(mesa_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{mesa_id}", status_code=status.HTTP_200_OK)
def obter_mesa_admin(
    mesa_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin),  # se for protegido
):
    repo = MesaRepositorio(db)
    m = repo.get_mesa_por_id(mesa_id)
    if not m:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    status_str, status_id = _status_from_mesa(m)
    return {
        "id": m.id,
        "uuid": m.uuid,
        "nome": m.nome,
        "status": status_str,
        "status_id": status_id,
        "created_at": getattr(m, "created_at", None),
        "updated_at": getattr(m, "updated_at", None),
    }

@router.get("/{mesa_id}/status", status_code=status.HTTP_200_OK)
def status_mesa_admin(
    mesa_id: int = Path(...),
    _: Restaurante = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    m = MesaRepositorio(db).get_mesa_por_id(mesa_id)
    if not m:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa não encontrada")
    status_str, status_id = _status_from_mesa(m)
    return {
        "mesa_id": m.id,
        "status": status_str,
        "status_id": status_id,
        "tem_pedidos": _tem_pedidos(db, m.id),
    }

@router.get("/{mesa_id}/pedidos")
def listar_pedidos_da_mesa_admin(
    mesa_id: int,
    status: str | None = Query(
        default=None,
        description="Lista separada por vírgula com status (ids ou textos). Ex: 1,2 ou pendente,preparo"
    ),
    desde: datetime | None = Query(
        default=None,
        description="Filtra a partir desta data/hora (ISO 8601). Ex: 2025-09-13T00:00:00"
    ),
    db: Session = Depends(get_db),
):
    repo_ped = RepositorioPedido(db)

    # Não filtra por status por padrão
    status_list = None
    if status:
        status_list = [s.strip() for s in status.split(",") if s.strip()]

    pedidos = repo_ped.listar_por_mesa(mesa_id, status_list, desde)
    return pedidos

@router.post("/{mesa_id}/status", status_code=status.HTTP_200_OK)
def alterar_status_mesa_admin(
    mesa_id: int = Path(...),
    payload: dict = Body(...),
    _: Restaurante = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        status_id_in = int(payload.get("status_id", 0))
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "status_id inválido")

    repo = MesaRepositorio(db)
    m = repo.alterar_status(mesa_id, status_id_in)

    status_str, status_id_calc = _status_from_mesa(m)
    return {
        "success": True,
        "mesa": {
            "id": m.id,
            "uuid": m.uuid,
            "status": status_str,
            "status_id": status_id_calc,
            "updated_at": _iso8601(getattr(m, "updated_at", None)),
        }
    }

@router.post("/{mesa_id}/encerrar", status_code=status.HTTP_200_OK)
def encerrar_mesa_admin(
    mesa_id: int = Path(...),
    req: MesaFechamentoRequest = Body(...),
    _: Restaurante = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # precisa ter pedidos ATIVOS
    ativos = (
        db.query(ModelPedido)
        .filter(
            ModelPedido.mesa_id == mesa_id,
            ModelPedido.status_id != 4   # 4 = concluído/fechado
        )
        .count()
    )
    if ativos == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Mesa não possui pedidos abertos")

    metodo = req.metodo_pagamento

    repo_ped = RepositorioPedido(db)
    pedidos, total = repo_ped.fechar_conta(mesa_id, metodo)   # agora soma só “abertos”

    mrepo = MesaRepositorio(db)
    m = mrepo.limpar_sessao_voltar_disponivel(mesa_id)

    return {
        "success": True,
        "fechamento": {
            "mesa_id": mesa_id,
            "valor_total": float(total or 0.0),
            "metodo_pagamento": metodo,
            "fechado_em": _iso8601(datetime.now(timezone.utc)),
        },
        "mesa": {"status": "disponivel", "status_id": 1}
    }
