from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.orm import Session, selectinload

from src.infra.sqlalchemy.models import (
    pedido as model_pedido,
    item_pedido as model_item,
    produto as model_produto
)
from src.schemas.pedidos import PedidoCreate

class RepositorioPedido:
    def __init__(self, db: Session):
        self.db = db

    def criar_pedido(self, mesa_id: int, dados: PedidoCreate):
        agora = datetime.utcnow()
        estimativa = agora + timedelta(minutes=15)
        cabecalho = model_pedido.Pedido(
            mesa_id=mesa_id,
            timestamp=agora,
            status="confirmado",
            observacoes_gerais=dados.observacoesGerais,
            valor_total=0.0,
            estimativa_entrega=estimativa
        )
        self.db.add(cabecalho)
        self.db.flush()

        total = 0.0
        for i in dados.itens:
            produto = self.db.get(model_produto.Produto, i.produtoId)
            subtotal = float(produto.preco) * i.quantidade
            total += subtotal
            item = model_item.ItemPedido(
                pedido_id=cabecalho.id,
                produto_id=produto.id,
                quantidade=i.quantidade,
                preco_unitario=float(produto.preco),
                observacoes=i.observacoes,
                subtotal=subtotal
            )
            self.db.add(item)

        cabecalho.valor_total = total
        self.db.commit()

        # eager-load dos itens e produtos
        self.db.refresh(cabecalho)
        for item in cabecalho.itens:
            _ = item.produto.nome

        return cabecalho

    def buscar_por_id(self, pedido_id: int):
        stmt = (
            select(model_pedido.Pedido)
            .where(model_pedido.Pedido.id == pedido_id)
            .options(
                selectinload(model_pedido.Pedido.itens)
                .selectinload(model_item.ItemPedido.produto)
            )
        )
        return self.db.scalars(stmt).first()

    def remover(self, pedido_id: int) -> bool:
        # exclui itens antes do cabeçalho
        del_items = delete(model_item.ItemPedido).where(
            model_item.ItemPedido.pedido_id == pedido_id
        )
        self.db.execute(del_items)

        stmt = delete(model_pedido.Pedido).where(
            model_pedido.Pedido.id == pedido_id
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

    def listar_por_mesa(
        self,
        mesa_id: int,
        status: str | None = None,
        desde: datetime | None = None
    ):
        stmt = (
            select(model_pedido.Pedido)
            .where(model_pedido.Pedido.mesa_id == mesa_id)
        )
        if status:
            stmt = stmt.where(model_pedido.Pedido.status == status)
        if desde:
            stmt = stmt.where(model_pedido.Pedido.timestamp >= desde)
        stmt = stmt.options(
            selectinload(model_pedido.Pedido.itens)
            .selectinload(model_item.ItemPedido.produto)
        )
        return self.db.scalars(stmt).all()

    def fechar_conta(self, mesa_id: int, forma_pagamento: str):
        """
        Marca todos os pedidos da mesa como 'concluido',
        soma o valor total e retorna (lista_de_pedidos, total).
        """
        pedidos = self.listar_por_mesa(mesa_id, status=None, desde=None)
        total = sum(p.valor_total for p in pedidos)
        for p in pedidos:
            p.status = "concluido"
            # opcional: armazenar forma_pagamento em cada pedido
            self.db.add(p)
        self.db.commit()
        return pedidos, total

    def atualizar_status(
        self,
        pedido_id: int,
        status: str,
        mensagem: Optional[str] = None
    ):
        pedido = self.buscar_por_id(pedido_id)
        if not pedido:
            return None
        pedido.status = status
        pedido.atualizado_em = datetime.utcnow()
        # se houver coluna para mensagem, poderia armazenar aqui
        self.db.add(pedido)
        self.db.commit()
        self.db.refresh(pedido)
        return pedido
