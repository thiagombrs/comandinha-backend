from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session, selectinload
from src.infra.sqlalchemy.models import produto as model_produto
from src.schemas.produto import ProdutoCreate

class RepositorioProduto:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, dados: ProdutoCreate):
        # Usa model_dump sem alias para corresponder aos atributos do modelo SQLAlchemy
        data = dados.model_dump(by_alias=False)
        obj = model_produto.Produto(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def listar_por_categoria(self, categoria_id: int):
        stmt = (
            select(model_produto.Produto)
            .where(model_produto.Produto.categoria_id == categoria_id)
            .options(selectinload(model_produto.Produto.categoria))
        )
        return self.db.scalars(stmt).all()

    def listar_com_categorias(self):
        stmt = (
            select(model_produto.Produto)
            .options(selectinload(model_produto.Produto.categoria))
        )
        return self.db.scalars(stmt).all()

    def buscar_por_id(self, id: int):
        stmt = (
            select(model_produto.Produto)
            .where(model_produto.Produto.id == id)
            .options(selectinload(model_produto.Produto.categoria))
        )
        return self.db.scalars(stmt).first()

    def editar(self, id: int, dados: ProdutoCreate):
        # Usa model_dump sem alias para corresponder aos atributos do modelo SQLAlchemy
        data = dados.model_dump(by_alias=False)
        stmt = (
            update(model_produto.Produto)
            .where(model_produto.Produto.id == id)
            .values(**data)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

    def remover(self, id: int):
        stmt = delete(model_produto.Produto).where(model_produto.Produto.id == id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

    def listar_recomendados(self, limite: int):
        stmt = (
            select(model_produto.Produto)
            .where(model_produto.Produto.popular == True)
            .limit(limite)
            .options(selectinload(model_produto.Produto.categoria))
        )
        return self.db.scalars(stmt).all()