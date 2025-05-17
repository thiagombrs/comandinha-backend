from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from src.infra.sqlalchemy.models.categoria import Categoria
from src.schemas.categoria import CategoriaCreate

class CategoriaRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, dto: CategoriaCreate) -> Categoria:
        nova = Categoria(
            nome=dto.nome,
            descricao=dto.descricao,
            imagem_url=dto.imagem_url,
            ordem=dto.ordem,
        )
        self.db.add(nova)
        self.db.commit()
        self.db.refresh(nova)
        return nova

    def listar(self, somente_ativas: bool = True):
        stmt = select(Categoria)
        if somente_ativas:
            stmt = stmt.where(Categoria.ativa == True)
        stmt = stmt.order_by(Categoria.ordem)
        return self.db.scalars(stmt).all()

    def buscar_por_id(self, id: int) -> Categoria | None:
        stmt = (
            select(Categoria)
            .where(Categoria.id == id)
            .options(selectinload(Categoria.produtos))
        )
        return self.db.scalars(stmt).first()

    def remover(self, id: int) -> bool:
        categoria = self.db.get(Categoria, id)
        if not categoria:
            return False
        self.db.delete(categoria)
        self.db.commit()
        return True
