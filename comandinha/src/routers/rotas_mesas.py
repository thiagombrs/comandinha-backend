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

bearer_scheme = HTTPBearer()
router = APIRouter(prefix="/mesas", tags=["mesas"])


@router.get(
    "",
    response_model=List[MesaListResponse],
    status_code=status.HTTP_200_OK
)
def listar_mesas_endpoint(
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
                nome=m.nome,
                status=status_str
            )
        )
    return resultado


@router.post("", response_model=MesaCriacaoResponse, status_code=status.HTTP_201_CREATED)
def criar_mesa_endpoint(
    req: MesaCriacaoRequest,
    db: Session = Depends(get_db)
):
    mesa = MesaRepositorio(db).criar_mesa(req.nome)
    return MesaCriacaoResponse(id=mesa.id, nome=mesa.nome)


@router.post("/ativar", response_model=MesaAtivacaoResponse)
def ativar_mesa_endpoint(
    req: MesaAtivacaoRequest,
    db: Session = Depends(get_db)
):
    mesa = MesaRepositorio(db).ativar_mesa(int(req.mesaId), req.codigoConfirmacao)
    return MesaAtivacaoResponse(
        token=mesa.token,
        expiraEm=mesa.expira_em,
        mesaId=str(mesa.id),
        mesaNome=mesa.nome
    )


@router.post(
    "/{mesa_id}/desativar",
    status_code=status.HTTP_204_NO_CONTENT
)
def desativar_mesa_endpoint(
    mesa_id: int = Path(...),
    cred: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db)
):
    mesa = MesaRepositorio(db).get_mesa_por_token(cred.credentials)
    if mesa.id != mesa_id:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Token não corresponde à mesa informada"
        )
    MesaRepositorio(db).desativar_mesa(mesa_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/validar", response_model=MesaValidacaoResponse)
def validar_mesa_endpoint(
    cred: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db)
):
    mesa = MesaRepositorio(db).validar_token(cred.credentials)
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
    cred: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db)
):
    mesa = MesaRepositorio(db).validar_token(cred.credentials)
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
    cred: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db)
):
    repo = MesaRepositorio(db)
    mesa = repo.get_mesa_por_token(cred.credentials)
    if mesa.id != mesa_id:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Token não corresponde à mesa informada"
        )
    mesa = repo.refresh_mesa(mesa.token)
    return MesaAtivacaoResponse(
        token=mesa.token,
        expiraEm=mesa.expira_em,
        mesaId=str(mesa.id),
        mesaNome=mesa.nome
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
    cred: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db),
):
    mesa = MesaRepositorio(db).validar_token(cred.credentials)
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


@router.post(
    "/{mesa_id}/fechar",
    response_model=MesaFechamentoResponse
)
def fechar_conta_endpoint(
    mesa_id: int = Path(...),
    req: MesaFechamentoRequest = Body(...),
    cred: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db)
):
    repo_mesa = MesaRepositorio(db)
    mesa = repo_mesa.validar_token(cred.credentials)
    if mesa.id != mesa_id:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Token não corresponde à mesa informada"
        )

    repo_ped = RepositorioPedido(db)
    pedidos_concluidos, total = repo_ped.fechar_conta(mesa_id, req.formaPagamento)
    repo_mesa.desativar_mesa(mesa_id)

    return MesaFechamentoResponse(
        mesaId=str(mesa_id),
        valorTotal=total,
        statusMesa="fechada"
    )


@router.delete(
    "/{mesa_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def excluir_mesa_endpoint(
    mesa_id: int = Path(...),
    db: Session = Depends(get_db)
):
    MesaRepositorio(db).excluir_mesa(mesa_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
