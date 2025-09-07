# src/routers/rotas_auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

from src.infra.sqlalchemy.config.database import get_db
from src.infra.sqlalchemy.repositorios.repositorio_restaurante import RepositorioRestaurante
from src.schemas.auth import AdminRegisterRequest, AdminLoginRequest, AdminRead, TokenResponse
from src.infra.providers.token_provider import TokenProvider, ACCESS_TOKEN_EXPIRE_MINUTES
from src.dependencies import get_current_admin
from src.infra.sqlalchemy.models.restaurante import Restaurante

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", response_model=AdminRead, status_code=status.HTTP_201_CREATED)
def register_admin(payload: AdminRegisterRequest, db: Session = Depends(get_db)):
    repo = RepositorioRestaurante(db)
    if repo.buscar_por_email(payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já cadastrado")
    senha_hash = pwd_context.hash(payload.senha)
    try:
        admin = repo.criar(nome=payload.nome, email=payload.email, senha_hash=senha_hash)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já cadastrado")
    return AdminRead.model_validate(admin, from_attributes=True)


@router.post("/login", response_model=TokenResponse)
def login_admin(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    repo = RepositorioRestaurante(db)
    admin = repo.buscar_por_email(payload.email)
    if not admin or not pwd_context.verify(payload.senha, admin.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = TokenProvider.criar_access_token({"sub": str(admin.id), "role": "admin"}, expires_delta=expires)
    return TokenResponse(access_token=token, token_type="bearer", expires_in=int(expires.total_seconds()))


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(admin: Restaurante = Depends(get_current_admin)):
    """
    Renova o access token usando o próprio token (stateless).
    Basta estar logado para emitir um novo token com novo 'exp'.
    """
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = TokenProvider.criar_access_token({"sub": str(admin.id), "role": "admin"}, expires_delta=expires)
    return TokenResponse(access_token=token, token_type="bearer", expires_in=int(expires.total_seconds()))
