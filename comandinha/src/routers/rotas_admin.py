from fastapi import APIRouter, Depends, status
from src.schemas.auth import AdminRead
from src.dependencies import get_current_admin
from src.infra.sqlalchemy.models.restaurante import Restaurante

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/me", response_model=AdminRead, status_code=status.HTTP_200_OK)
def admin_me(admin: Restaurante = Depends(get_current_admin)):
    return AdminRead.model_validate(admin, from_attributes=True)
