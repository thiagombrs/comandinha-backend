import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse
from src.infra.sqlalchemy.config.database import engine, Base

# Importa routers de cada recurso
from src.routers.rotas_mesas import router as mesas_router
from src.routers.rotas_categorias import router as categorias_router
from src.routers.rotas_produtos import router as produtos_router
from src.routers.rotas_pedidos import router as pedidos_router
from src.routers.rotas_chamados import router as chamados_router

app = FastAPI(
    title="API Comandinha",
    description="Backend do Projeto Comandinha",
    version="1.0.0"
)

# Configuração de CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handler para erros de validação da resposta
@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Response validation error",
            "details": exc.errors(),  # erros de schema
            "body": repr(exc.body)     # corpo original convertido em string
        }
    )

# Evento de startup: cria as tabelas no banco
@app.on_event("startup")
def on_startup():
    # importa modelos para registrar todas as tabelas
    import src.infra.sqlalchemy.models.mesa  # noqa: F401
    import src.infra.sqlalchemy.models.categoria  # noqa: F401
    import src.infra.sqlalchemy.models.produto  # noqa: F401
    import src.infra.sqlalchemy.models.pedido  # noqa: F401
    import src.infra.sqlalchemy.models.chamado_garcom  # noqa: F401
    Base.metadata.create_all(bind=engine)

# Health-check
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
# Registro de routers
app.include_router(mesas_router)
app.include_router(categorias_router)
app.include_router(produtos_router)
app.include_router(pedidos_router)
#app.include_router(chamados_router, prefix="/chamados", tags=["chamados"])

# Permite iniciar com `python server.py`
if __name__ == "__main__":
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
