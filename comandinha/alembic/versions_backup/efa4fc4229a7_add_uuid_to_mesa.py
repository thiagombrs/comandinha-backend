"""add uuid to mesa

Revision ID: efa4fc4229a7
Revises: 
Create Date: 2025-09-04 18:07:59.655610

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid

# --- Identificadores da revisão ---
revision = "efa4fc4229a7"   # use exatamente o ID do nome do arquivo
down_revision = None        # se houver uma migration anterior, troque pelo ID dela
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(c["name"] == column for c in insp.get_columns(table))


def _has_index(table: str, index: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(ix["name"] == index for ix in insp.get_indexes(table))


def upgrade():
    # 1) Garante a coluna 'uuid' (nullable=True inicialmente)
    if not _has_column("mesa", "uuid"):
        with op.batch_alter_table("mesa") as batch_op:
            batch_op.add_column(sa.Column("uuid", sa.String(length=36), nullable=True))

    # 2) Preenche UUID para linhas sem valor
    conn = op.get_bind()
    ids_sem_uuid = conn.execute(sa.text("SELECT id FROM mesa WHERE uuid IS NULL")).fetchall()
    for (mesa_id,) in ids_sem_uuid:
        novo_uuid = str(uuid.uuid4())
        conn.execute(
            sa.text("UPDATE mesa SET uuid = :u WHERE id = :i"),
            {"u": novo_uuid, "i": mesa_id}
        )

    # 3) Cria índice único (SQLite-friendly) e torna NOT NULL
    with op.batch_alter_table("mesa") as batch_op:
        if not _has_index("mesa", "ix_mesa_uuid_unique"):
            batch_op.create_index("ix_mesa_uuid_unique", ["uuid"], unique=True)
        batch_op.alter_column("uuid", existing_type=sa.String(length=36), nullable=False)


def downgrade():
    # Remove índice único e coluna
    with op.batch_alter_table("mesa") as batch_op:
        try:
            batch_op.drop_index("ix_mesa_uuid_unique")
        except Exception:
            pass
        batch_op.drop_column("uuid")
