from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de conexão com o SQLite para o arquivo de banco de dados
SQLALCHEMY_DATABASE_URL = "sqlite:///./app_comandinha.db"

# Criação do engine SQLAlchemy, permitindo múltiplas threads
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Configuração da SessionLocal para injeção de dependência
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Classe base para todas as models declarativas
Base = declarative_base()

# Dependência para obter sessão do DB em endpoints FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
