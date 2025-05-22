from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from src.schemas.produto import Adicional

class ItemPedidoCreate(BaseModel):
    produtoId: int = Field(..., alias="produtoId")
    quantidade: int
    observacoes: Optional[str] = None

    class Config:
        populate_by_name = True

class PedidoCreate(BaseModel):
    mesaId: int = Field(..., alias="mesaId")
    itens: List[ItemPedidoCreate]
    observacoesGerais: Optional[str] = Field(None, alias="observacoesGerais")

    class Config:
        populate_by_name = True

class ItemPedidoResponse(BaseModel):
    produtoId: int = Field(..., alias="produtoId")
    nome: str
    quantidade: int
    precoUnitario: float = Field(..., alias="precoUnitario")
    observacoes: Optional[str]
    subtotal: float

    class Config:
        populate_by_name = True

class PedidoResponse(BaseModel):
    pedidoId: int = Field(..., alias="pedidoId")
    timestamp: datetime
    status: str
    observacoesGerais: Optional[str]
    itens: List[ItemPedidoResponse]
    valorTotal: float = Field(..., alias="valorTotal")
    estimativaEntrega: datetime = Field(..., alias="estimativaEntrega")

    class Config:
        populate_by_name = True

class PedidoStatusUpdateRequest(BaseModel):
    status: str
    mensagem: Optional[str] = None

class PedidoStatusUpdateResponse(BaseModel):
    pedidoId: int = Field(..., alias="pedidoId")
    status: str
    atualizadoEm: datetime = Field(..., alias="atualizadoEm")

    class Config:
        populate_by_name = True

# Visão de produção
class ItemProducaoResponse(BaseModel):
    produtoNome: str = Field(..., alias="produtoNome")
    produtoDescricao: Optional[str] = Field(None, alias="produtoDescricao")
    produtoAdicionais: Optional[List[Adicional]] = Field(None, alias="produtoAdicionais")
    quantidade: int
    observacoes: Optional[str]

    class Config:
        populate_by_name = True

class PedidoProducaoResponse(BaseModel):
    pedidoId: int = Field(..., alias="pedidoId")
    mesaId: int = Field(..., alias="mesaId")
    mesaNome: str = Field(..., alias="mesaNome")
    timestamp: datetime
    status: str
    observacoesGerais: Optional[str]
    estimativaEntrega: datetime = Field(..., alias="estimativaEntrega")
    itens: List[ItemProducaoResponse]

    class Config:
        populate_by_name = True
