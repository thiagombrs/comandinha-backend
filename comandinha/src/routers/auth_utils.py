# src/routers/auth_utils.py

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from src.infra.sqlalchemy.config.database import get_db
from src.infra.sqlalchemy.repositorios.repositorio_mesa import MesaRepositorio
from src.infra.providers.token_provider import token_provider

def obter_token_mesa(authorization: str = Header(...)) -> str:
    """
    Extrai o token do header Authorization: Bearer {mesa_token}
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido ou formato inválido"
        )
    return authorization.split(" ", 1)[1]

def obter_mesa_logada(
    token: str = Depends(obter_token_mesa),
    db: Session = Depends(get_db)
):
    """
    Verifica o token de mesa e retorna a instância de Mesa.
    """
    try:
        # verify_mesa_token retorna diretamente o ID da mesa (int)
        mesa_id = token_provider.verify_mesa_token(token)
    except HTTPException:
        # Já foi tratado no provider
        raise
    except Exception:
        # Qualquer outro erro
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de mesa inválido ou expirado"
        )

    mesa = MesaRepositorio(db).get_mesa_por_id(mesa_id)
    if not mesa:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mesa não encontrada"
        )
    return mesa
