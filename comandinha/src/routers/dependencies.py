from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from src.infra.sqlalchemy.config.database import get_db
from src.infra.sqlalchemy.models.mesa import Mesa

def get_mesa_autenticada(
    authorization: str = Header(..., description="Bearer token da mesa"),
    db: Session = Depends(get_db)
):
    # extrai só o token (espera “Bearer {token}”)
    try:
        scheme, token = authorization.split()
        assert scheme.lower() == "bearer"
    except:
        raise HTTPException(401, "Cabeçalho Authorization inválido")
    mesa = db.query(Mesa).filter_by(token=token).first()
    if not mesa:
        raise HTTPException(401, "Mesa não autenticada")
    return mesa
