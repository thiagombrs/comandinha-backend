import os
from contextlib import contextmanager

from sqlalchemy import create_engine, MetaData, Table, select, text
from sqlalchemy.engine import Connection

# Ajuste se o arquivo sqlite estiver em outro lugar
SQLITE_URL = "sqlite:///./app_comandinha.db"
POSTGRES_URL = os.getenv("DATABASE_URL")  # já definido no seu ambiente

BATCH_SIZE = 1000  # tamanho do lote para inserts

def log(msg: str):
    print(f"[migrate] {msg}")

@contextmanager
def connect(url: str):
    eng = create_engine(url, pool_pre_ping=True)
    conn = eng.connect()
    try:
        yield conn
    finally:
        conn.close()
        eng.dispose()

def reflect_metadata(conn: Connection) -> MetaData:
    md = MetaData()
    md.reflect(bind=conn)
    return md

def copy_table(src_conn: Connection, dst_conn: Connection, table: Table):
    """Copia dados de uma tabela do SQLite para o Postgres em lotes."""
    # Conta registros de origem
    total = src_conn.execute(select(text("COUNT(1)")).select_from(table)).scalar_one()
    if total == 0:
        log(f"{table.name}: origem vazia (0 linhas)")
        return

    log(f"{table.name}: copiando {total} linhas...")

    # Seleciona em páginas
    offset = 0
    cols = list(table.c)

    # Monta a tabela de destino pelo mesmo nome
    dst_table = Table(table.name, MetaData(), autoload_with=dst_conn)

    while offset < total:
        rows = src_conn.execute(
            select(*cols).offset(offset).limit(BATCH_SIZE)
        ).mappings().all()

        if not rows:
            break

        # Insert em lote
        dst_conn.execute(dst_table.insert(), rows)
        dst_conn.commit()

        offset += len(rows)
        log(f"{table.name}: {offset}/{total}")

    # Se a tabela tiver uma PK autoincremento, ajusta a sequence
    # Funciona para colunas SERIAL/IDENTITY padrão com nome <tabela>_<coluna>_seq
    pk_cols = [c for c in dst_table.c if c.primary_key]
    if len(pk_cols) == 1 and pk_cols[0].autoincrement:
        pk = pk_cols[0].name
        seq_name = f"{dst_table.name}_{pk}_seq"
        try:
            max_id = dst_conn.execute(select(text(f"MAX({pk})")).select_from(dst_table)).scalar()
            if max_id:
                dst_conn.execute(text(f"SELECT setval(:seq, :val, true)"), {"seq": seq_name, "val": int(max_id)})
                dst_conn.commit()
                log(f"{table.name}: sequence '{seq_name}' setada para {max_id}")
        except Exception as e:
            # Se a sequence tiver outro nome/IDENTITY, ignoramos silenciosamente
            log(f"{table.name}: não foi possível ajustar sequence ({e})")

def main():
    assert POSTGRES_URL, "Defina a variável de ambiente DATABASE_URL apontando para o Postgres."

    with connect(SQLITE_URL) as src, connect(POSTGRES_URL) as dst:
        # Garante chaves estrangeiras desligadas no SQLite para leitura bulk
        src.execute(text("PRAGMA foreign_keys=OFF"))
        # Habilita constraints no Postgres (já é padrão), mas garantimos explicitamente
        dst.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))

        # Carrega metadados (tabelas) da origem, e usa a ordem respeitando FKs
        src_md = reflect_metadata(src)
        if not src_md.tables:
            log("Nenhuma tabela encontrada no SQLite. Verifique o caminho do arquivo.")
            return

        # A ordem correta é fornecida por sorted_tables (pais antes de filhos)
        for table in src_md.sorted_tables:
            # Pula metadados internos do SQLite, se houver
            if table.name.startswith("sqlite_"):
                continue
            copy_table(src, dst, table)

    log("Migração concluída com sucesso.")

if __name__ == "__main__":
    main()
