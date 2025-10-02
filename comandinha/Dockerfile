FROM bitnami/python:3.11
WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# expõe a porta 4000 (mesma que vamos usar no CMD)
EXPOSE 4000

# inicia o uvicorn apontando para server.py no root
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "4000", "--reload", "--reload-dir", "src"]
