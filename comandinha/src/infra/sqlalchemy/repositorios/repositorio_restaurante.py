from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.infra.sqlalchemy.models.restaurante import Restaurante

class RepositorioRestaurante:
    def __init__(self, db: Session):
        self.db = db

    def buscar_por_email(self, email: str) -> Optional[Restaurante]:
        stmt = select(Restaurante).where(Restaurante.email == email)
        return self.db.scalars(stmt).first()

    def buscar_por_id(self, admin_id: int) -> Optional[Restaurante]:
        return self.db.get(Restaurante, admin_id)

    def criar(self, nome: str, email: str, senha_hash: str) -> Restaurante:
        obj = Restaurante(nome=nome, email=email, senha_hash=senha_hash)
        self.db.add(obj)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise
        self.db.refresh(obj)
        return obj
