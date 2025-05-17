# src/schemas/chamado.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChamadoCreateRequest(BaseModel):
    motivo: str
    detalhes: Optional[str] = None

    class Config:
        from_attributes = True

class ChamadoRead(BaseModel):
    id: int
    mesa_id: int
    motivo: str
    detalhes: Optional[str]
    status: str
    timestamp: datetime

    class Config:
        orm_mode = True
        from_attributes = True
