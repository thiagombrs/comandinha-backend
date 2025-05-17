from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "sua_chave_secreta_aqui"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Extrator padrão para token de usuário
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
# Extrator para token de mesa
mesa_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/mesas/ativar")

class TokenProvider:
    @staticmethod
    def criar_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


    def verify_access_token(token: str = Depends(oauth2_scheme)) -> str:
        creds_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            sub = payload.get("sub")
            if sub is None:
                raise creds_exc
        except JWTError:
            raise creds_exc
        return sub  # aqui seu LoginData.sub (por exemplo telefone)


    @staticmethod
    def verify_mesa_token(token: str) -> int:
        creds_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de mesa inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            mesa_id = payload.get("mesa_id")
            if mesa_id is None:
                raise creds_exc
        except JWTError:
            raise creds_exc
        return int(mesa_id)
    
token_provider = TokenProvider()


