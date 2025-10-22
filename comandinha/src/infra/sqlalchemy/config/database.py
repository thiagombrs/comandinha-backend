# src/infra/sqlalchemy/config/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Se DATABASE_URL não existir, mantemos SQLite local (dev)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app_comandinha.db")

engine_kwargs = {"pool_pre_ping": True}  # evita conexões zumbis

# Argumento específico do SQLite
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
