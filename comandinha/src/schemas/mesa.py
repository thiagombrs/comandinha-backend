# src/schemas/mesa.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MesaCriacaoRequest(BaseModel):
    nome: str

class MesaCriacaoResponse(BaseModel):
    id: int
    nome: str

    class Config:
        from_attributes = True

class MesaAtivacaoRequest(BaseModel):
    mesaId: str
    codigoConfirmacao: Optional[str] = None

class MesaAtivacaoResponse(BaseModel):
    token: str
    expiraEm: datetime
    mesaId: str
    mesaNome: str

    class Config:
        from_attributes = True

class MesaValidacaoResponse(BaseModel):
    valido: bool
    expiraEm: datetime
    mesaId: str

    class Config:
        from_attributes = True

class MesaFechamentoRequest(BaseModel):
    formaPagamento: str

class MesaFechamentoResponse(BaseModel):
    mesaId: str
    valorTotal: float
    statusMesa: str

    class Config:
        from_attributes = True

class MesaListResponse(BaseModel):
    id: int
    nome: str
    status: str

    class Config:
        from_attributes = True
