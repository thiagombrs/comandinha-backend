from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# ⚠️ Em produção, mova esta chave para variável de ambiente (.env)
SECRET_KEY = "sua_chave_secreta_aqui"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Apenas para fins de documentação / Swagger (não usamos diretamente nas dependências)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
mesa_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/mesas/ativar")


class TokenProvider:
    @staticmethod
    def criar_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """
        Gera um JWT com 'exp' e os claims recebidos em 'data'.
        Ex.: data={"sub": "1", "role": "admin"}
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_access_token(token: str) -> str:
        """
        Valida o JWT de ADMIN. Retorna o 'sub' (id do admin) se válido.
        Lança HTTP 401 se token inválido/expirado/sem 'sub'.
        """
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
            return sub
        except JWTError:
            raise creds_exc

    @staticmethod
    def verify_mesa_token(token: str) -> int:
        """
        (Opcional) Valida o JWT de MESA, retornando 'mesa_id' se existir.
        Útil se você optar por JWT para mesas; caso use token opaco (DB),
        apenas não use este método.
        """
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
            return int(mesa_id)
        except JWTError:
            raise creds_exc


# Instância para compatibilidade com imports existentes (se houver)
token_provider = TokenProvider()
