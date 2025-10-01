from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.orm import Session
from typing import List
from src.infra.sqlalchemy.config.database import get_db
from src.infra.sqlalchemy.repositorios.repositorio_chamado import RepositorioChamado
from src.schemas.chamado import CriarChamadoMesaRequest, ChamadoResponse

from typing import List, Optional, Union
from datetime import datetime
from fastapi import Query
from typing import List 

# >>> IMPORTS de auth/admin como em rotas_pedidos
from src.infra.sqlalchemy.models.restaurante import Restaurante
from src.dependencies import get_current_admin

router = APIRouter(prefix="", tags=["chamadas"])

@router.post("/chamadas", response_model=ChamadoResponse, status_code=status.HTTP_201_CREATED)
def criar_chamada_mesa(req: CriarChamadoMesaRequest, db: Session = Depends(get_db)):
    repo = RepositorioChamado(db)
    try:
        ch = repo.criar(req.mesa_uuid, req.motivo, req.detalhes)
        return repo.to_response_dict(ch)
    except ValueError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))

@router.get("/chamadas/historico", response_model=List[ChamadoResponse])
def historico_chamadas_admin(
    status: Optional[Union[int, str]] = Query(
        None,
        description="Filtro de status: código 1|2|3 ou texto pendente|atendida|cancelada"
    ),
    mesa_uuid: Optional[str] = Query(None, description="Filtra por uma mesa específica (UUID)"),
    desde: Optional[datetime] = Query(None, description="ISO 8601. Ex: 2025-09-22T00:00:00"),
    admin: Restaurante = Depends(get_current_admin),   # exige bearer admin
    db: Session = Depends(get_db),
):
    repo = RepositorioChamado(db)
    try:
        itens = repo.historico(desde=desde, status=status, mesa_uuid=mesa_uuid)  # <-- ver nota abaixo
        return [repo.to_response_dict(ch) for ch in itens]
    except ValueError as e:
        # status inválido, etc.
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.patch("/chamadas/{chamado_id}/cancelar", response_model=ChamadoResponse)
def cancelar_chamada_mesa(
    chamado_id: int = Path(...),
    mesa_uuid: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    repo = RepositorioChamado(db)
    try:
        ch = repo.cancelar_da_mesa(chamado_id, mesa_uuid)
        return repo.to_response_dict(ch)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

# >>> EXIGE ADMIN (bearer) AQUI
@router.patch("/chamadas/{chamado_id}/atender", response_model=ChamadoResponse)
def atender_chamada_admin(
    chamado_id: int,
    admin: Restaurante = Depends(get_current_admin),  # <- exige bearer admin
    db: Session = Depends(get_db),
):
    repo = RepositorioChamado(db)
    try:
        # passa id/uuid do admin para registro
        admin_ident = getattr(admin, "uuid", None) or getattr(admin, "id", None) or "admin"
        ch = repo.atender(chamado_id, admin_ident=admin_ident)
        return repo.to_response_dict(ch)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/chamadas/pendentes", response_model=List[ChamadoResponse])
def listar_chamadas_pendentes(
    admin: Restaurante = Depends(get_current_admin),   # exige bearer admin
    db: Session = Depends(get_db),
):
    repo = RepositorioChamado(db)
    itens = repo.listar_pendentes()
    return [repo.to_response_dict(ch) for ch in itens]


@router.get("/mesas/uuid/{mesa_uuid}/chamadas", response_model=List[ChamadoResponse])
def historico_da_mesa(mesa_uuid: str, db: Session = Depends(get_db)):
    repo = RepositorioChamado(db)
    itens = repo.historico_da_mesa(mesa_uuid)
    return [repo.to_response_dict(ch) for ch in itens]