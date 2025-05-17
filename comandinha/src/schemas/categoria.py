from pydantic import BaseModel, Field
from typing import Optional

class CategoriaCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    imagem_url: Optional[str] = Field(None, alias="imagemUrl")
    ordem: int

    class Config:
        from_attributes = True
        allow_population_by_field_name = True


class CategoriaSimples(BaseModel):
    id: int
    nome: str
    descricao: Optional[str]
    imagem_url: Optional[str] = Field(None, alias="imagemUrl")
    ordem: int

    class Config:
        from_attributes = True
        allow_population_by_field_name = True


class CategoriaRead(CategoriaSimples):
    """Esquema de leitura de categoria idêntico a CategoriaSimples."""
    pass
