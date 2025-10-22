# Base estável e leve
FROM python:3.11-slim

# Configs básicas
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_MODULE=${APP_MODULE:-server:app} \
    PORT=${PORT:-8000}

WORKDIR /app

# Dependências de build (mínimas; adicione mais se precisar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Instala as libs Python
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copia o projeto
COPY . /app

# Porta exposta (Render usa $PORT)
EXPOSE 8000

# Sobe o app (ajuste APP_MODULE se seu app não for server:app)
CMD bash -lc "alembic upgrade head && uvicorn server:app --host 0.0.0.0 --port $PORT"

