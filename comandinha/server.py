import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.infra.sqlalchemy.config.database import engine, Base

# importa routers
from src.routers.rotas_mesas import router as mesas_router
from src.routers.rotas_categorias import router as categorias_router
from src.routers.rotas_produtos import router as produtos_router
from src.routers.rotas_pedidos import router as pedidos_router
from src.routers.rotas_auth import router as auth_router
from src.routers.rotas_admin import router as admin_router
from src.routers.rotas_chamados import router as chamados_router

# from src.routers.rotas_chamados import router as chamados_router  # opcional

app = FastAPI(
    title="API Comandinha",
    description="Backend do Projeto Comandinha",
    version="1.0.0"
)

# CORS — permitir apenas os domínios especificados
origins = [
    "http://localhost:3000",
    "https://barao-comandinha.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # registra todos os modelos para criar tabelas
    import src.infra.sqlalchemy.models.mesa  # noqa: F401
    import src.infra.sqlalchemy.models.categoria  # noqa: F401
    import src.infra.sqlalchemy.models.produto  # noqa: F401
    import src.infra.sqlalchemy.models.pedido  # noqa: F401
    import src.infra.sqlalchemy.models.chamado_garcom  # noqa: F401
    import src.infra.sqlalchemy.models.chamado_garcom 
    Base.metadata.create_all(bind=engine)

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

# registra routers
app.include_router(mesas_router)
app.include_router(categorias_router)
app.include_router(produtos_router)
app.include_router(pedidos_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(chamados_router)

# permite rodar com "python server.py"
if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=4000,
        reload=True,
        reload_dirs=["src"]
    )
