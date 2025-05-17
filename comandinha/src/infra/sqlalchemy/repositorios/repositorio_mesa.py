# src/infra/sqlalchemy/repositorios/repositorio_mesa.py

from sqlalchemy.orm import Session
from sqlalchemy import select, delete as sa_delete
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from typing import Optional, List

from src.infra.sqlalchemy.models.mesa import Mesa
from src.infra.sqlalchemy.models.pedido import Pedido as ModelPedido
from src.infra.providers.token_provider import token_provider

class MesaRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def criar_mesa(self, nome: str) -> Mesa:
        mesa = Mesa(nome=nome)
        self.db.add(mesa)
        self.db.commit()
        self.db.refresh(mesa)
        return mesa

    def listar_mesas(self) -> List[Mesa]:
        stmt = select(Mesa)
        return self.db.scalars(stmt).all()

    def get_mesa_por_id(self, mesa_id: int) -> Optional[Mesa]:
        return self.db.get(Mesa, mesa_id)

    def get_mesa_por_token(self, token: str) -> Mesa:
        stmt = select(Mesa).where(Mesa.token == token)
        mesa = self.db.scalars(stmt).first()
        if not mesa:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de mesa inválido"
            )
        return mesa

    def ativar_mesa(
        self,
        mesa_id: int,
        codigo_confirmacao: Optional[str] = None,
        validade_minutos: int = 60
    ) -> Mesa:
        mesa = self.get_mesa_por_id(mesa_id)
        if not mesa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mesa {mesa_id} não existe"
            )
        if mesa.ativo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mesa já está ativa"
            )

        expires_delta = timedelta(minutes=validade_minutos)
        token = token_provider.criar_access_token(
            {"mesa_id": mesa.id},
            expires_delta
        )
        mesa.token     = token
        mesa.expira_em = datetime.utcnow() + expires_delta
        mesa.ativo     = True

        self.db.add(mesa)
        self.db.commit()
        self.db.refresh(mesa)
        return mesa

    def validar_token(self, token: str) -> Mesa:
        try:
            mesa_id = token_provider.verify_mesa_token(token)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de mesa inválido ou expirado"
            )

        mesa = self.get_mesa_por_id(mesa_id)
        if not mesa:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Mesa não encontrada"
            )
        return mesa

    def desativar_mesa(self, mesa_id: int) -> Mesa:
        mesa = self.get_mesa_por_id(mesa_id)
        if not mesa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mesa {mesa_id} não existe"
            )
        if not mesa.ativo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mesa já está desativada"
            )

        mesa.ativo     = False
        mesa.token     = None
        mesa.expira_em = None

        self.db.add(mesa)
        self.db.commit()
        self.db.refresh(mesa)
        return mesa

    def excluir_mesa(self, mesa_id: int) -> None:
        mesa = self.get_mesa_por_id(mesa_id)
        if not mesa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mesa {mesa_id} não existe"
            )
        if mesa.ativo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Só é possível excluir mesas desativadas"
            )
        pendentes = (
            self.db.query(ModelPedido)
            .filter(
                ModelPedido.mesa_id == mesa_id,
                ModelPedido.status != "concluido"
            )
            .count()
        )
        if pendentes > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível excluir mesa com pedidos não concluídos"
            )
        # deleta pedidos concluídos
        self.db.execute(
            sa_delete(ModelPedido).where(ModelPedido.mesa_id == mesa_id)
        )
        self.db.commit()
        mesa = self.get_mesa_por_id(mesa_id)
        self.db.delete(mesa)
        self.db.commit()

    def refresh_mesa(
        self,
        token: str,
        validade_minutos: int = 60
    ) -> Mesa:
        mesa = self.get_mesa_por_token(token)
        expires_delta = timedelta(minutes=validade_minutos)
        mesa.expira_em = datetime.utcnow() + expires_delta
        self.db.add(mesa)
        self.db.commit()
        self.db.refresh(mesa)
        return mesa
