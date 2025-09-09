from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from sqlalchemy.orm import Session

from src.infra.sqlalchemy.config.database import get_db
from src.infra.sqlalchemy.repositorios.repositorio_categoria import CategoriaRepositorio
from src.infra.sqlalchemy.repositorios.repositorio_produto import RepositorioProduto

from src.schemas.categoria import CategoriaCreate, CategoriaSimples, CategoriaUpdate
from src.schemas.produto import ProdutoSimples

# proteção admin
from src.dependencies import get_current_admin
from src.infra.sqlalchemy.models.restaurante import Restaurante

router = APIRouter(
    prefix="/categorias",
    tags=["categorias"]
)

# --------- ESCRITA (PROTEGIDA) ---------

@router.post(
    "",
    response_model=CategoriaSimples,
    status_code=status.HTTP_201_CREATED
)
def criar_categoria(
    categoria: CategoriaCreate,
    db: Session = Depends(get_db),
    _: Restaurante = Depends(get_current_admin),  # requer admin
):
    repo = CategoriaRepositorio(db)
    obj = repo.criar(categoria)
    schema = CategoriaSimples.model_validate(obj, from_attributes=True, by_name=True)
    return schema.model_dump(by_alias=True)


@router.put(
    "/{id}",
    response_model=CategoriaSimples
)
def atualizar_categoria(
    id: int,
    categoria: CategoriaCreate,
    db: Session = Depends(get_db),
    _: Restaurante = Depends(get_current_admin),  # requer admin
):
    repo = CategoriaRepositorio(db)
    updated = repo.editar(id, categoria)
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Categoria {id} não encontrada")
    obj = repo.buscar_por_id(id)
    schema = CategoriaSimples.model_validate(obj, from_attributes=True, by_name=True)
    return schema.model_dump(by_alias=True)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remover_categoria(
    id: int,
    db: Session = Depends(get_db),
    _: Restaurante = Depends(get_current_admin),  # requer admin
):
    repo = CategoriaRepositorio(db)
    ok = repo.remover(id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Categoria {id} não encontrada")


# --------- LEITURA (PÚBLICA) ---------

@router.get(
    "",
    response_model=List[CategoriaSimples]
)
def listar_categorias(
    db: Session = Depends(get_db)
):
    repo = CategoriaRepositorio(db)
    objs = repo.listar()
    return [
        CategoriaSimples
            .model_validate(o, from_attributes=True, by_name=True)
            .model_dump(by_alias=True)
        for o in objs
    ]


@router.get(
    "/{id}",
    response_model=CategoriaSimples
)
def exibir_categoria(
    id: int,
    db: Session = Depends(get_db)
):
    repo = CategoriaRepositorio(db)
    obj = repo.buscar_por_id(id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Categoria {id} não encontrada")
    schema = CategoriaSimples.model_validate(obj, from_attributes=True, by_name=True)
    return schema.model_dump(by_alias=True)


@router.get(
    "/{categoriaId}/produtos",
    response_model=List[ProdutoSimples]
)
def listar_produtos_por_categoria(
    categoriaId: int,
    populares: bool = Query(False),
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db)
):
    repo_cat = CategoriaRepositorio(db)
    categoria = repo_cat.buscar_por_id(categoriaId)
    if not categoria:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Categoria {categoriaId} não encontrada")

    repo_prod = RepositorioProduto(db)
    produtos = repo_prod.listar_por_categoria(categoriaId)

    return [
        ProdutoSimples
            .model_validate(p, from_attributes=True, by_name=True)
            .model_dump(by_alias=True)
        for p in produtos
    ]


@router.patch("/{id}", response_model=CategoriaSimples)
def atualizar_categoria_parcial(
    id: int,
    patch: CategoriaUpdate,
    db: Session = Depends(get_db),
    _: Restaurante = Depends(get_current_admin),
):
    repo = CategoriaRepositorio(db)
    obj = repo.buscar_por_id(id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Categoria {id} não encontrada")

    # >>> use by_alias=False para garantir 'imagem_url'
    data = patch.model_dump(exclude_unset=True, by_alias=False)
    for k, v in data.items():
        setattr(obj, k, v)

    db.commit()
    db.refresh(obj)
    return CategoriaSimples.model_validate(obj, from_attributes=True, by_name=True).model_dump(by_alias=True)