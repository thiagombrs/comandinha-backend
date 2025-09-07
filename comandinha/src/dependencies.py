from fastapi import Depends, HTTPException, Header, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.infra.sqlalchemy.config.database import get_db
from src.infra.sqlalchemy.models.mesa import Mesa
from src.infra.sqlalchemy.repositorios.repositorio_restaurante import RepositorioRestaurante
from src.infra.providers.token_provider import TokenProvider

_bearer = HTTPBearer(auto_error=True)


def get_current_admin(
    cred: HTTPAuthorizationCredentials = Security(_bearer),
    db: Session = Depends(get_db),
):
    """
    Extrai 'Authorization: Bearer <jwt>' do header,
    valida o token e carrega o admin do banco.
    """
    token = cred.credentials
    sub = TokenProvider.verify_access_token(token)

    try:
        admin_id = int(sub)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    admin = RepositorioRestaurante(db).buscar_por_id(admin_id)
    if not admin:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Admin não encontrado")

    return admin


def get_mesa_autenticada(
    authorization: str = Header(..., description="Bearer token da mesa"),
    db: Session = Depends(get_db),
):
    """
    Suporta dois modos:
    - Token JWT contendo 'mesa_id' (usa TokenProvider.verify_mesa_token)
    - Token opaco salvo em Mesa.token (consulta direta ao banco)
    """
    # Tenta extrair 'Bearer <token>' do header
    try:
        scheme, raw_token = authorization.split()
        assert scheme.lower() == "bearer"
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Cabeçalho Authorization inválido")

    # 1) Tenta como JWT de mesa
    try:
        mesa_id = TokenProvider.verify_mesa_token(raw_token)
        mesa = db.get(Mesa, mesa_id)
        if mesa is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Mesa não encontrada")
        return mesa
    except HTTPException:
        # 2) Se não for JWT válido, trata como token opaco (DB)
        mesa = db.query(Mesa).filter_by(token=raw_token).first()
        if not mesa:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Mesa não autenticada")
        return mesa
