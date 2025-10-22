import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

def _normalize_db_url(url: str) -> str:
    if not url:
        return url or ""

    # 1) Troca qualquer variante psycopg3 por psycopg2
    #    (cobre 'postgresql+psycopg://', 'postgresql+psycopg:' e até casos estranhos)
    url = re.sub(r"^postgresql\+psycopg(?!2)", "postgresql+psycopg2", url)

    # 2) Converte 'postgres://' legada para 'postgresql+psycopg2://'
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)

    # 3) Se vier como 'postgresql://' sem driver explícito, força +psycopg2
    if url.startswith("postgresql://") and "+psycopg" not in url and "+pg8000" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

    return url

DATABASE_URL = _normalize_db_url(os.getenv("DATABASE_URL", ""))

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
