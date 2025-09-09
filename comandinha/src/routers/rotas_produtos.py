# src/routers/rotas_produtos.py

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.infra.sqlalchemy.config.database import get_db
from src.infra.sqlalchemy.repositorios.repositorio_produto import RepositorioProduto
from src.schemas.produto import ProdutoCreate, ProdutoSimples, ProdutoDetalhado, ProdutoUpdate

# proteção admin
from src.dependencies import get_current_admin
from src.infra.sqlalchemy.models.restaurante import Restaurante

router = APIRouter(
    prefix="/produtos",
    tags=["produtos"]
)

# --------- ESCRITA (PROTEGIDA) ---------

@router.post(
    "",
    response_model=ProdutoSimples,
    status_code=status.HTTP_201_CREATED
)
def criar_produto(
    produto: ProdutoCreate,
    db: Session = Depends(get_db),
    _: Restaurante = Depends(get_current_admin),  # requer admin
):
    repo = RepositorioProduto(db)
    obj = repo.criar(produto)
    return ProdutoSimples \
        .model_validate(obj, from_attributes=True, by_name=True) \
        .model_dump(by_alias=True)


@router.put(
    "/{id}",
    response_model=ProdutoSimples
)
def atualizar_produto(
    id: int,
    produto: ProdutoCreate,
    db: Session = Depends(get_db),
    _: Restaurante = Depends(get_current_admin),  # requer admin
):
    repo = RepositorioProduto(db)
    if not repo.editar(id, produto):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Produto {id} não encontrado")
    obj = repo.buscar_por_id(id)
    return ProdutoSimples \
        .model_validate(obj, from_attributes=True, by_name=True) \
        .model_dump(by_alias=True)

@router.patch(
    "/{id}",
    response_model=ProdutoSimples
)
def atualizar_produto_parcial(
    id: int,
    patch: ProdutoUpdate,
    db: Session = Depends(get_db),
    _: Restaurante = Depends(get_current_admin),  # requer admin
):
    repo = RepositorioProduto(db)
    obj = repo.buscar_por_id(id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Produto {id} não encontrado")

    # chaves no formato do ORM (sem alias) para bater com as colunas do modelo
    data = patch.model_dump(exclude_unset=True, by_alias=False)
    if not repo.editar_parcial(id, data):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Produto {id} não encontrado")
    obj = repo.buscar_por_id(id)

    db.commit()
    db.refresh(obj)
    return ProdutoSimples.model_validate(obj, from_attributes=True, by_name=True).model_dump(by_alias=True)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remover_produto(
    id: int,
    db: Session = Depends(get_db),
    _: Restaurante = Depends(get_current_admin),  # requer admin
):
    repo = RepositorioProduto(db)
    if not repo.remover(id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Produto {id} não encontrado")


# --------- LEITURA (PÚBLICA) ---------

@router.get(
    "",
    response_model=List[ProdutoDetalhado]
)
def listar_produtos(
    categoria_id: Optional[int] = Query(None, alias="categoriaId"),
    db: Session = Depends(get_db)
):
    repo = RepositorioProduto(db)
    if categoria_id is not None:
        objs = repo.listar_por_categoria(categoria_id)
    else:
        objs = repo.listar_com_categorias()
    return [
        ProdutoDetalhado
            .model_validate(o, from_attributes=True, by_name=True)
            .model_dump(by_alias=True)
        for o in objs
    ]

@router.get(
    "/recomendados",
    response_model=List[ProdutoSimples],
    status_code=status.HTTP_200_OK
)
def listar_recomendados(
    limite: int = Query(5, ge=1, le=50, description="Máximo de itens a retornar"),
    db: Session = Depends(get_db)
):
    repo = RepositorioProduto(db)
    recomendados = repo.listar_recomendados(limite)
    return [
        ProdutoSimples
            .model_validate(p, from_attributes=True, by_name=True)
            .model_dump(by_alias=True)
        for p in recomendados
    ]


@router.get(
    "/{id}",
    response_model=ProdutoDetalhado
)
def exibir_produto(
    id: int,
    db: Session = Depends(get_db)
):
    repo = RepositorioProduto(db)
    obj = repo.buscar_por_id(id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Produto {id} não encontrado")
    return ProdutoDetalhado \
        .model_validate(obj, from_attributes=True, by_name=True) \
        .model_dump(by_alias=True)


@router.get("", response_model=List[ProdutoDetalhado])
def listar_produtos(
    categoria_id: int | None = Query(None, alias="categoriaId"),
    somente_disponiveis: bool = Query(False, alias="somenteDisponiveis"),
    db: Session = Depends(get_db),
):
    repo = RepositorioProduto(db)
    objs = repo.listar_por_categoria(categoria_id) if categoria_id else repo.listar_com_categorias()
    if somente_disponiveis:
        objs = [o for o in objs if getattr(o, "disponivel", True)]
    return [ProdutoDetalhado.model_validate(o, from_attributes=True, by_name=True).model_dump(by_alias=True) for o in objs]

