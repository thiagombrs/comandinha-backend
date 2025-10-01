from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Request: MOTIVO = int (1..3)
class CriarChamadoMesaRequest(BaseModel):
    mesa_uuid: str = Field(..., description="UUID da mesa")
    motivo: int = Field(..., ge=1, le=3, description="1=assistencia, 2=fechar_conta, 3=urgente")
    detalhes: Optional[str] = None

# Response: strings (como você pediu)
class ChamadoResponse(BaseModel):
    id: int
    mesa_uuid: str
    motivo: str            # <-- string
    status: str            # <-- string
    detalhes: Optional[str]
    criado_em: datetime
    atendido_em: Optional[datetime] = None
    cancelado_em: Optional[datetime] = None
    atendido_por: Optional[str] = None

    # (Se quiser expor também os códigos, adicione campos motivo_code/status_code aqui.)

    model_config = {"from_attributes": True}
