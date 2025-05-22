from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List

from src.infra.sqlalchemy.config.database import get_db
from src.infra.sqlalchemy.repositorios.repositorio_pedido import RepositorioPedido
from src.schemas.pedidos import (
    PedidoCreate,
    PedidoResponse,
    PedidoStatusUpdateRequest,
    PedidoStatusUpdateResponse,
    PedidoProducaoResponse,
    ItemProducaoResponse
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
    db: Session = Depends(get_db),
):
    """
    Cria um pedido para a mesa indicada em pedido_create.mesaId.
    """
    repo = RepositorioPedido(db)
    pedido = repo.criar_pedido(pedido_create.mesaId, pedido_create)

    # Eager-load dos itens e nome do produto
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
    "/producao",
    response_model=List[PedidoProducaoResponse],
    status_code=status.HTTP_200_OK
)
def listar_pedidos_producao(
    db: Session = Depends(get_db),
):
    """
    Lista todos os pedidos em status 'confirmado' ou 'preparando' para a produção.
    """
    repo = RepositorioPedido(db)
    pedidos = repo.listar_para_producao()

    resposta: List[PedidoProducaoResponse] = []
    for p in pedidos:
        db.refresh(p)
        # Eager-load mesa e itens
        _ = p.mesa.nome
        for item in p.itens:
            _ = item.produto.nome

        resposta.append(PedidoProducaoResponse(
            pedidoId=p.id,
            mesaId=p.mesa.id,
            mesaNome=p.mesa.nome,
            timestamp=p.timestamp,
            status=p.status,
            observacoesGerais=p.observacoes_gerais,
            estimativaEntrega=p.estimativa_entrega,
            itens=[
                ItemProducaoResponse(
                    produtoNome=item.produto.nome,
                    produtoDescricao=item.produto.descricao,
                    produtoAdicionais=item.produto.adicionais,
                    quantidade=item.quantidade,
                    observacoes=item.observacoes,
                )
                for item in p.itens
            ]
        ))
    return resposta

@router.get(
    "/{pedido_id}",
    response_model=PedidoResponse,
    status_code=status.HTTP_200_OK
)
def exibir_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtém os detalhes de um pedido por ID.
    """
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
    db: Session = Depends(get_db),
):
    """
    Remove um pedido e seus itens.
    """
    repo = RepositorioPedido(db)
    ok = repo.remover(pedido_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido {pedido_id} não encontrado"
        )

@router.patch(
    "/{pedido_id}/status",
    response_model=PedidoStatusUpdateResponse,
    status_code=status.HTTP_200_OK
)
def atualizar_status_pedido(
    pedido_id: int,
    status_req: PedidoStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Atualiza o status de um pedido.
    """
    repo = RepositorioPedido(db)
    atualizado = repo.atualizar_status(
        pedido_id,
        status_req.status,
        status_req.mensagem
    )
    if not atualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido {pedido_id} não encontrado"
        )
    return PedidoStatusUpdateResponse(
        pedidoId=atualizado.id,
        status=atualizado.status,
        atualizadoEm=atualizado.atualizado_em
    )
