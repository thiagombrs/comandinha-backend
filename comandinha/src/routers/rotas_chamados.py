# src/routers/rotas_chamados.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.infra.sqlalchemy.config.database import get_db
from src.infra.sqlalchemy.repositorios.repositorio_chamado import RepositorioChamado
from src.schemas.chamado import ChamadoCreateRequest, ChamadoRead
from src.routers.auth_utils import obter_mesa_logada

router = APIRouter()

@router.post(
    "/", 
    status_code=status.HTTP_201_CREATED, 
    response_model=ChamadoRead
)
def chamar_garcom(
    mesa=Depends(obter_mesa_logada),
    chamado_req: ChamadoCreateRequest = Depends(),
    db: Session = Depends(get_db)
):
    # grava o chamado
    chamado = RepositorioChamado(db).criar_chamado(
        mesa_id=mesa.id,
        motivo=chamado_req.motivo,
        detalhes=chamado_req.detalhes,
    )
    return chamado

@router.get(
    "/{chamado_id}", 
    response_model=ChamadoRead
)
def obter_chamado(
    chamado_id: int,
    mesa=Depends(obter_mesa_logada),
    db: Session = Depends(get_db)
):
    chamado = RepositorioChamado(db).buscar_por_id(chamado_id)
    if not chamado or chamado.mesa_id != mesa.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado não encontrado"
        )
    return chamado
