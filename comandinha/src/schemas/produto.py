from pydantic import BaseModel, Field
from typing import Optional, List
from src.schemas.categoria import CategoriaSimples

class Adicional(BaseModel):
    id: str
    nome: str
    preco: float

    class Config:
        from_attributes = True

class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    popular: bool = False
    imagem_url: Optional[str] = Field(None, alias="imagemUrl")
    tempo_preparo_minutos: Optional[int] = Field(None, alias="tempoPreparoMinutos")
    restricoes: Optional[List[str]] = []
    adicionais: Optional[List[Adicional]] = []

    disponivel: bool = True

    class Config:
        from_attributes = True
        allow_population_by_field_name = True

class ProdutoCreate(ProdutoBase):
    categoria_id: int = Field(..., alias="categoriaId")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class ProdutoSimples(ProdutoBase):
    id: int
    categoria_id: int = Field(..., alias="categoriaId")

    class Config:
        from_attributes = True
        allow_population_by_field_name = True

class ProdutoDetalhado(ProdutoSimples):
    categoria: CategoriaSimples

    class Config:
        from_attributes = True
        allow_population_by_field_name = True

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    popular: Optional[bool] = None
    imagem_url: Optional[str] = Field(None, alias="imagemUrl")
    tempo_preparo_minutos: Optional[int] = Field(None, alias="tempoPreparoMinutos")
    restricoes: Optional[List[str]] = None
    adicionais: Optional[List[Adicional]] = None
    categoria_id: Optional[int] = Field(None, alias="categoriaId")

    disponivel: Optional[bool] = None

    class Config:
        from_attributes = True
        allow_population_by_field_name = True