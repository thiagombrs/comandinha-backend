from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class AdminRegisterRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=6, max_length=128)

class AdminLoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=6, max_length=128)

class AdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = None  # em segundos
