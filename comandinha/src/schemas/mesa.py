from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class MesaCriacaoRequest(BaseModel):
    nome: str

class MesaCriacaoResponse(BaseModel):
    id: int
    uuid: str
    nome: str
    status: str | None = None
    status_id: int | None = None
    
    class Config:
        from_attributes = True

class MesaAtivacaoRequest(BaseModel):
    mesaId: str
    codigoConfirmacao: Optional[str] = None

class MesaAtivacaoResponse(BaseModel):
    token: str
    expiraEm: datetime
    mesaId: int
    mesaNome: str
    uuid: str

    class Config:
        from_attributes = True

class MesaValidacaoResponse(BaseModel):
    valido: bool
    expiraEm: Optional[datetime] = None
    mesaId: str

    class Config:
        from_attributes = True

class MesaFechamentoRequest(BaseModel):
    metodo_pagamento: Optional[str] = Field(default=None, alias="metodo_pagamento")
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class MesaFechamentoResponse(BaseModel):
    mesaId: str
    valorTotal: float
    statusMesa: str

    class Config:
        from_attributes = True

class MesaListResponse(BaseModel):
    id: int
    uuid: str
    nome: str
    status: str
    status_id: int

    class Config:
        from_attributes = True
