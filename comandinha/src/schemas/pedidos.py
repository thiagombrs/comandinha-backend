# src/schemas/pedido.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class ItemPedidoCreate(BaseModel):
    produtoId: int = Field(..., alias="produtoId")
    quantidade: int
    observacoes: Optional[str] = None

    class Config:
        populate_by_name = True

class PedidoCreate(BaseModel):
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
    pedidoId: str = Field(..., alias="pedidoId")
    status: str
    atualizadoEm: datetime = Field(..., alias="atualizadoEm")

    class Config:
        populate_by_name = True