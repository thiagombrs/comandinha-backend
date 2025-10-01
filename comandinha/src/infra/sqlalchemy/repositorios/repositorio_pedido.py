from datetime import datetime, timedelta
from typing import Optional, List

from typing import Optional, List, Union, Iterable
from sqlalchemy import select, and_, or_

from sqlalchemy import select, delete
from sqlalchemy.orm import Session, selectinload

from src.infra.sqlalchemy.models.pedido import Pedido
from src.infra.sqlalchemy.models.item_pedido import ItemPedido
from src.infra.sqlalchemy.models.mesa import Mesa

from fastapi import HTTPException


from src.infra.sqlalchemy.models import (
    pedido as model_pedido,
    item_pedido as model_item,
    produto as model_produto
)
from src.schemas.pedidos import PedidoCreate

class RepositorioPedido:
    def __init__(self, db: Session):
        self.db = db

    def atualizar_status_id(self, pedido_id: int, status_id: int):
        p = self.db.get(model_pedido.Pedido, pedido_id)
        if not p:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        if status_id not in (1, 2, 3, 4):
            raise HTTPException(status_code=400, detail="status_id inválido (use 1..4)")

        p.status_id = status_id            # sincroniza 'status' via @validates
        p.atualizado_em = datetime.utcnow()
        self.db.add(p)
        self.db.commit()
        self.db.refresh(p)
        return p
    
    def criar_pedido(self, mesa_id: int, dados: PedidoCreate):
        from datetime import datetime, timedelta
        agora = datetime.utcnow()
        estimativa = agora + timedelta(minutes=15)

        cabecalho = model_pedido.Pedido(
            mesa_id=mesa_id,
            status_id=1,                # pendente
            timestamp=agora,
            atualizado_em=agora,
            estimativa_entrega=estimativa,
            observacoes_gerais=dados.observacoesGerais,
            valor_total=0.0,
        )

        self.db.add(cabecalho)
        self.db.flush()

        total = 0.0
        for i in dados.itens:
            produto = self.db.get(model_produto.Produto, i.produtoId)
            if not produto:
                raise HTTPException(status_code=404, detail=f"Produto {i.produtoId} não encontrado")

            preco_unit = float(produto.preco)
            subtotal = preco_unit * i.quantidade
            total += subtotal

            item = model_item.ItemPedido(
                pedido_id=cabecalho.id,
                produto_id=produto.id,
                quantidade=i.quantidade,
                preco_unitario=preco_unit,
                observacoes=i.observacoes,
                subtotal=subtotal,
            )
            self.db.add(item)

        cabecalho.valor_total = total
        self.db.commit()

        self.db.refresh(cabecalho)
        for item in cabecalho.itens:
            _ = item.produto.nome

        # ✅ pós-criação: marcar mesa como EM_USO (2), se não estiver desativada (4)
        mesa = self.db.get(Mesa, mesa_id)
        if not mesa:
            raise HTTPException(status_code=404, detail="Mesa não encontrada")
        if getattr(mesa, "status_id", 1) != 4:
            mesa.status_id = 2
            self.db.add(mesa)
            self.db.commit()
            self.db.refresh(mesa)

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

    from typing import Union

    def listar_por_mesa(
        self,
        mesa_id: int,
        status: Optional[Iterable[Union[str, int]]] = None,
        desde: Optional[datetime] = None,
    ) -> List[Pedido]:
        """
        Lista pedidos de uma mesa. Se 'status' for fornecido, aceita IDs (1..4) e/ou
        textos ('pendente','preparo','entregue','concluido'). Se não vier, não filtra por status.
        """
        q = self.db.query(Pedido).filter(Pedido.mesa_id == mesa_id)

        if status:
            status_ids: List[int] = []
            status_texts: List[str] = []
            for s in status:
                if isinstance(s, int):
                    status_ids.append(s)
                elif isinstance(s, str) and s.isdigit():
                    status_ids.append(int(s))
                elif isinstance(s, str):
                    status_texts.append(s.strip().lower())

            # Aplica os dois filtros com OR (qualquer um que bater)
            if status_ids and status_texts:
                q = q.filter(
                    (Pedido.status_id.in_(status_ids))
                    | (Pedido.status.in_(status_texts))
                )
            elif status_ids:
                q = q.filter(Pedido.status_id.in_(status_ids))
            elif status_texts:
                q = q.filter(Pedido.status.in_(status_texts))

        if desde:
            q = q.filter(Pedido.timestamp >= desde)

        return q.order_by(Pedido.timestamp.desc()).all()


    def listar_para_producao(self) -> List[model_pedido.Pedido]:
        """
        Retorna todos os pedidos PENDENTES/EM_PREPARO (1,2),
        com relacionamento de mesa, itens e produtos carregados.
        """
        stmt = (
            select(model_pedido.Pedido)
            .where(model_pedido.Pedido.status_id.in_([1, 2]))
            .options(
                selectinload(model_pedido.Pedido.mesa),
                selectinload(model_pedido.Pedido.itens)
                .selectinload(model_item.ItemPedido.produto)
            )
        )
        return self.db.scalars(stmt).all()


    def fechar_conta(self, mesa_id: int, forma_pagamento: str):
    # pega todos os pedidos abertos da mesa (qualquer status_id diferente de 4)
        pedidos_abertos = (
            self.db.query(Pedido)
            .filter(Pedido.mesa_id == mesa_id, Pedido.status_id != 4)
            .all()
        )

        if not pedidos_abertos:
            return [], 0.0

        total = sum(float(p.valor_total or 0.0) for p in pedidos_abertos)

        # marca todos como concluído (4)
        agora = datetime.utcnow()
        for p in pedidos_abertos:
            p.status_id = 4
            p.atualizado_em = agora
            self.db.add(p)

        self.db.commit()
        return pedidos_abertos, total


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
        self.db.add(pedido)
        self.db.commit()
        self.db.refresh(pedido)
        return pedido

    def listar_nao_concluidos(self):
        stmt = (
            select(model_pedido.Pedido)
            .where(model_pedido.Pedido.status_id != 4)
            .order_by(model_pedido.Pedido.timestamp.desc())
        )
        return self.db.scalars(stmt).all()
    
    def limpar_todos(self) -> int:
        # 1º itens (FK), depois pedidos
        self.db.execute(delete(model_item.ItemPedido))
        result = self.db.execute(delete(model_pedido.Pedido))
        self.db.commit()
        return result.rowcount