from fastapi import APIRouter, HTTPException, status, Depends, Path, Body
from sqlalchemy.orm import Session
from typing import List

from src.infra.sqlalchemy.config.database import get_db
from src.infra.sqlalchemy.repositorios.repositorio_pedido import RepositorioPedido
from src.infra.sqlalchemy.repositorios.repositorio_mesa import MesaRepositorio
from src.schemas.pedidos import (
    PedidoCreate,
    PedidoResponse,
    PedidoStatusUpdateRequest,
    PedidoStatusUpdateResponse,
    PedidoProducaoResponse,
    ItemProducaoResponse
)

from src.schemas.pedidos import PedidoStatusPatchRequest, PedidoStatusPatchResponse
from src.infra.sqlalchemy.models.restaurante import Restaurante
from src.dependencies import get_current_admin

router = APIRouter(
    prefix="/pedidos",
    tags=["pedidos"]
)

@router.get(
    "",
    response_model=List[PedidoProducaoResponse],
    status_code=status.HTTP_200_OK
)
def listar_pedidos_nao_concluidos(
    _: Restaurante = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Lista todos os pedidos ainda não concluídos (admin),
    incluindo itens no mesmo formato de /pedidos/producao.
    """
    repo = RepositorioPedido(db)
    pedidos = repo.listar_nao_concluidos()

    resposta: List[PedidoProducaoResponse] = []
    for p in pedidos:
        # Força carregamento das relações para evitar lazy-load fora da sessão
        db.refresh(p)
        _ = p.mesa.nome  # mesa
        for item in p.itens:
            _ = item.produto.nome  # produto

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
            ],
        ))
    return resposta

@router.post(
    "",
    response_model=PedidoResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_pedido(
    pedido_create: PedidoCreate,
    db: Session = Depends(get_db),
):
    """
    Cria um pedido para a mesa identificada por UUID (cliente).
    """
    # Resolve mesa pelo UUID
    mrepo = MesaRepositorio(db)
    mesa = mrepo.get_mesa_por_uuid(pedido_create.uuid)
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    if getattr(mesa, "status_id", 1) == 4 or getattr(mesa, "ativo", True) is False:
        raise HTTPException(status_code=400, detail="Mesa desativada")

    repo = RepositorioPedido(db)
    pedido = repo.criar_pedido(mesa.id, pedido_create)

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
    _: Restaurante = Depends(get_current_admin),
):
    repo = RepositorioPedido(db)
    ok = repo.remover(pedido_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pedido {pedido_id} não encontrado"
        )

@router.patch("/{pedido_id}/status", response_model=PedidoStatusPatchResponse)
def atualizar_status_pedido(
    pedido_id: int = Path(...),
    req: PedidoStatusPatchRequest = Body(...),
    _: Restaurante = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    repo = RepositorioPedido(db)
    p = repo.atualizar_status_id(pedido_id, req.status_id)
    return {"status": p.status, "status_id": p.status_id}

# === NOVO: limpar tudo (somente ADMIN) ===
@router.delete("", status_code=status.HTTP_200_OK)
def limpar_todos_pedidos(
    db: Session = Depends(get_db),
    _: Restaurante = Depends(get_current_admin),
):
    repo = RepositorioPedido(db)
    total = repo.limpar_todos()
    return {"mensagem": f"{total} pedidos removidos com sucesso"}