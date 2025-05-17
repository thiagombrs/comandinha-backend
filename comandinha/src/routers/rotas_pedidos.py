from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from src.routers.dependencies import get_mesa_autenticada
from src.infra.sqlalchemy.config.database import get_db
from src.infra.sqlalchemy.repositorios.repositorio_pedido import RepositorioPedido
from src.schemas.pedidos import (
    PedidoCreate,
    PedidoResponse,
    PedidoStatusUpdateRequest,
    PedidoStatusUpdateResponse
)

router = APIRouter(
    prefix="/pedidos",
    tags=["pedidos"]
)

@router.post(
    "/",
    response_model=PedidoResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_pedido(
    pedido_create: PedidoCreate,
    mesa = Depends(get_mesa_autenticada),
    db: Session = Depends(get_db),
):
    repo = RepositorioPedido(db)
    pedido = repo.criar_pedido(mesa.id, pedido_create)

    # eager-load itens/produtos
    db.refresh(pedido)
    for item in pedido.itens:
        _ = item.produto.nome

    return PedidoResponse(
        pedidoId=pedido.id,
        timestamp=pedido.timestamp,
        status=pedido.status,
        observacoesGerais=pedido.observacoes_gerais,
        itens=[
            {
                "produtoId": item.produto_id,
                "nome": item.produto.nome,
                "quantidade": item.quantidade,
                "precoUnitario": item.preco_unitario,
                "observacoes": item.observacoes,
                "subtotal": item.subtotal,
            }
            for item in pedido.itens
        ],
        valorTotal=pedido.valor_total,
        estimativaEntrega=pedido.estimativa_entrega
    )

@router.get(
    "/{pedido_id}",
    response_model=PedidoResponse,
    status_code=status.HTTP_200_OK
)
def exibir_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
):
    repo = RepositorioPedido(db)
    pedido = repo.buscar_por_id(pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido {pedido_id} não encontrado"
        )

    db.refresh(pedido)
    for item in pedido.itens:
        _ = item.produto.nome

    return PedidoResponse(
        pedidoId=pedido.id,
        timestamp=pedido.timestamp,
        status=pedido.status,
        observacoesGerais=pedido.observacoes_gerais,
        itens=[
            {
                "produtoId": item.produto_id,
                "nome": item.produto.nome,
                "quantidade": item.quantidade,
                "precoUnitario": item.preco_unitario,
                "observacoes": item.observacoes,
                "subtotal": item.subtotal,
            }
            for item in pedido.itens
        ],
        valorTotal=pedido.valor_total,
        estimativaEntrega=pedido.estimativa_entrega
    )

@router.delete(
    "/{pedido_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remover_pedido(
    pedido_id: int,
    mesa = Depends(get_mesa_autenticada),
    db: Session = Depends(get_db),
):
    repo = RepositorioPedido(db)
    ok = repo.remover(pedido_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido {pedido_id} não encontrado"
        )
    return

# ================================================
# 12. Atualizar Status do Pedido
# ================================================
@router.patch(
    "/{pedido_id}/status",
    response_model=PedidoStatusUpdateResponse,
    status_code=status.HTTP_200_OK
)
def atualizar_status_pedido(
    pedido_id: int,
    status_req: PedidoStatusUpdateRequest,
    mesa = Depends(get_mesa_autenticada),
    db: Session = Depends(get_db),
):
    repo = RepositorioPedido(db)
    pedido = repo.buscar_por_id(pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido {pedido_id} não encontrado"
        )
    # só a mesa que criou o pedido pode atualizá-lo
    if pedido.mesa_id != mesa.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não autorizado para este pedido"
        )
    updated = repo.atualizar_status(pedido_id, status_req.status)
    return PedidoStatusUpdateResponse(
        pedidoId=str(updated.id),
        status=updated.status,
        atualizadoEm=updated.atualizado_em
    )
