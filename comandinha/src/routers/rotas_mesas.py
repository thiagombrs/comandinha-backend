# rotas_mesas.py

from fastapi import (
    APIRouter, Depends, HTTPException, status, Response,
    Security, Path, Query, Body
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from src.schemas.mesa import (
    MesaCriacaoRequest,
    MesaCriacaoResponse,
    MesaListResponse,
    MesaAtivacaoRequest,
    MesaAtivacaoResponse,
    MesaValidacaoResponse,
    MesaFechamentoRequest,
    MesaFechamentoResponse,
)
from src.schemas.pedidos import PedidoResponse
from src.infra.sqlalchemy.config.database import get_db
from src.infra.sqlalchemy.repositorios.repositorio_mesa import MesaRepositorio
from src.infra.sqlalchemy.repositorios.repositorio_pedido import RepositorioPedido
from src.infra.providers.token_provider import token_provider

from src.dependencies import get_current_admin
from src.infra.sqlalchemy.models.restaurante import Restaurante

# Dois esquemas de Bearer: um para ADMIN e outro para MESA
bearer_admin = HTTPBearer(auto_error=True)
bearer_mesa  = HTTPBearer(auto_error=True)

router = APIRouter(prefix="/mesas", tags=["mesas"])


# ---------- Dependências de segurança ----------

def require_admin(
    cred: HTTPAuthorizationCredentials = Security(bearer_admin),
):
    """Valida o token de ADMIN."""
    try:
        token_provider.verify_admin_token(cred.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de admin inválido ou expirado"
        )
    return cred.credentials


def require_mesa_token(
    cred: HTTPAuthorizationCredentials = Security(bearer_mesa),
):
    """Obtém o token da MESA (validação detalhada ocorre nas rotas)."""
    if not cred or not cred.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de mesa ausente"
        )
    return cred.credentials


# ---------- ROTAS (ADMIN) ----------

@router.get(
    "",
    response_model=List[MesaListResponse],
    status_code=status.HTTP_200_OK
)
def listar_mesas_endpoint(
    _: Restaurante = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    repo = MesaRepositorio(db)
    mesas = repo.listar_mesas()
    agora = datetime.utcnow()
    resultado = []
    for m in mesas:
        if m.token is None:
            status_str = "disponível"
        elif m.expira_em and m.expira_em < agora:
            status_str = "expirada"
        else:
            status_str = "em uso"
        resultado.append(
            MesaListResponse(
                id=m.id,
                uuid=m.uuid,
                nome=m.nome,
                status=status_str
            )
        )
    return resultado


@router.post("", response_model=MesaCriacaoResponse, status_code=status.HTTP_201_CREATED)
def criar_mesa_endpoint(
    req: MesaCriacaoRequest,
    _: Restaurante = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    mesa = MesaRepositorio(db).criar_mesa(req.nome)
    return MesaCriacaoResponse(id=mesa.id, uuid=mesa.uuid, nome=mesa.nome)


@router.post("/{mesa_id}/encerrar", status_code=status.HTTP_204_NO_CONTENT)
def encerrar_sessao_mesa(
    mesa_id: int,
    _: Restaurante = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    repo = MesaRepositorio(db)
    ok = repo.encerrar_sessao(mesa_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa não encontrada")


@router.delete(
    "/{mesa_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def excluir_mesa_endpoint(
    mesa_id: int = Path(...),
    _: Restaurante = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    MesaRepositorio(db).excluir_mesa(mesa_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# >>> Ajustadas para ADMIN <<<
@router.post(
    "/{mesa_id}/desativar",
    status_code=status.HTTP_204_NO_CONTENT
)
def desativar_mesa_endpoint_admin(
    mesa_id: int = Path(...),
    _: Restaurante = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Desativa a mesa (admin força o encerramento da sessão).
    """
    MesaRepositorio(db).desativar_mesa(mesa_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{mesa_id}/fechar",
    response_model=MesaFechamentoResponse
)
def fechar_conta_endpoint_admin(
    mesa_id: int = Path(...),
    req: MesaFechamentoRequest = Body(...),
    _: Restaurante = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Admin fecha a conta da mesa (calcula total e conclui pedidos) e desativa a mesa.
    """
    repo_ped = RepositorioPedido(db)
    pedidos_concluidos, total = repo_ped.fechar_conta(mesa_id, req.formaPagamento)

    repo_mesa = MesaRepositorio(db)
    repo_mesa.desativar_mesa(mesa_id)

    return MesaFechamentoResponse(
        mesaId=str(mesa_id),
        valorTotal=total,
        statusMesa="fechada"
    )


# ---------- ROTAS (PÚBLICAS - fluxo QR/UUID) ----------

@router.post("/ativar", response_model=MesaAtivacaoResponse)
def ativar_mesa_endpoint(
    req: MesaAtivacaoRequest,
    db: Session = Depends(get_db)
):
    mesa = MesaRepositorio(db).ativar_mesa(int(req.mesaId), req.codigoConfirmacao)
    return MesaAtivacaoResponse(
        token=mesa.token,
        expiraEm=mesa.expira_em,
        mesaId=mesa.id,
        mesaNome=mesa.nome,
        uuid=mesa.uuid
    )


@router.get("/uuid/{mesa_uuid}", response_model=MesaListResponse)
def obter_mesa_por_uuid(
    mesa_uuid: str,
    db: Session = Depends(get_db)
):
    repo = MesaRepositorio(db)
    mesa = repo.get_mesa_por_uuid(mesa_uuid)
    if not mesa:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa não encontrada")

    agora = datetime.utcnow()
    status_str = "disponível"
    if mesa.token:
        if mesa.expira_em and mesa.expira_em < agora:
            status_str = "expirada"
        else:
            status_str = "em uso"

    return MesaListResponse(
        id=mesa.id,
        uuid=mesa.uuid,
        nome=mesa.nome,
        status=status_str
    )


@router.post("/uuid/{mesa_uuid}/ativar", response_model=MesaAtivacaoResponse)
def ativar_mesa_por_uuid(
    mesa_uuid: str,
    db: Session = Depends(get_db)
):
    repo = MesaRepositorio(db)
    mesa = repo.ativar_por_uuid(mesa_uuid)
    if not mesa:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa não encontrada")
    return MesaAtivacaoResponse(
        token=mesa.token,
        expiraEm=mesa.expira_em,
        mesaId=mesa.id,
        mesaNome=mesa.nome,
        uuid=mesa.uuid
    )


@router.get("/uuid/{mesa_uuid}/validar", response_model=MesaAtivacaoResponse)
def validar_mesa_por_uuid(
    mesa_uuid: str,
    db: Session = Depends(get_db)
):
    """
    Retorna status atual da mesa (se tem token e se está expirado).
    Útil pro front decidir se precisa reativar.
    """
    repo = MesaRepositorio(db)
    mesa = repo.get_mesa_por_uuid(mesa_uuid)
    if not mesa:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa não encontrada")

    if mesa.token and mesa.expira_em and mesa.expira_em > datetime.utcnow():
        # sessão válida
        return MesaAtivacaoResponse(
            token=mesa.token,
            expiraEm=mesa.expira_em,
            mesaId=mesa.id,
            mesaNome=mesa.nome,
            uuid=mesa.uuid
        )
    else:
        # sessão inválida/expirada — retorna 401 para o front saber que precisa ativar
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão expirada ou inexistente")


# ---------- ROTAS (MESA / CLIENTE) ----------

@router.get("/validar", response_model=MesaValidacaoResponse)
def validar_mesa_endpoint(
    mesa_token: str = Depends(require_mesa_token),
    db: Session = Depends(get_db)
):
    mesa = MesaRepositorio(db).validar_token(mesa_token)
    return MesaValidacaoResponse(
        valido=True,
        expiraEm=mesa.expira_em,
        mesaId=str(mesa.id)
    )


@router.get(
    "/{mesa_id}/status",
    response_model=MesaValidacaoResponse,
    status_code=status.HTTP_200_OK
)
def status_mesa_endpoint(
    mesa_id: int = Path(...),
    mesa_token: str = Depends(require_mesa_token),
    db: Session = Depends(get_db)
):
    mesa = MesaRepositorio(db).validar_token(mesa_token)
    if mesa.id != mesa_id:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Token não corresponde à mesa informada"
        )
    return MesaValidacaoResponse(
        valido=True,
        expiraEm=mesa.expira_em,
        mesaId=str(mesa.id)
    )


@router.post(
    "/{mesa_id}/refresh",
    response_model=MesaAtivacaoResponse
)
def refresh_mesa_endpoint(
    mesa_id: int = Path(...),
    mesa_token: str = Depends(require_mesa_token),
    db: Session = Depends(get_db)
):
    repo = MesaRepositorio(db)
    mesa = repo.get_mesa_por_token(mesa_token)
    if mesa.id != mesa_id:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Token não corresponde à mesa informada"
        )
    mesa = repo.refresh_mesa(mesa.token)
    return MesaAtivacaoResponse(
        token=mesa.token,
        expiraEm=mesa.expira_em,
        mesaId=mesa.id,
        mesaNome=mesa.nome,
        uuid=mesa.uuid
    )


@router.get(
    "/{mesa_id}/pedidos",
    status_code=status.HTTP_200_OK
)
def listar_pedidos_da_mesa(
    mesa_id: int = Path(...),
    status_filter: str = Query(
        "todos",
        regex="^(todos|confirmado|preparando|entregue)$"
    ),
    desde: Optional[datetime] = Query(None),
    mesa_token: str = Depends(require_mesa_token),
    db: Session = Depends(get_db),
):
    mesa = MesaRepositorio(db).validar_token(mesa_token)
    if mesa.id != mesa_id:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Token não corresponde à mesa informada"
        )

    repo_ped = RepositorioPedido(db)
    status_arg = None if status_filter == "todos" else status_filter
    pedidos = repo_ped.listar_por_mesa(mesa_id, status_arg, desde)

    return {
        "pedidos": [
            PedidoResponse(
                pedidoId=p.id,
                timestamp=p.timestamp,
                status=p.status,
                observacoesGerais=p.observacoes_gerais,
                itens=[{
                    "produtoId": item.produto_id,
                    "nome": item.produto.nome,
                    "quantidade": item.quantidade,
                    "precoUnitario": item.preco_unitario,
                    "observacoes": item.observacoes,
                    "subtotal": item.subtotal,
                } for item in p.itens],
                valorTotal=p.valor_total,
                estimativaEntrega=p.estimativa_entrega
            )
            for p in pedidos
        ]
    }
