"""create restaurantes

Revision ID: b187103d2454
Revises: efa4fc4229a7
Create Date: 2025-09-05 09:57:09.847236

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision = "b187103d2454"
down_revision = "efa4fc4229a7"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1) cria tabela só se não existir
    if not insp.has_table("restaurantes"):
        op.create_table(
            "restaurantes",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("nome", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False, unique=True),
            sa.Column("senha_hash", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    # 2) garante índice único em email (só se não houver)
    if insp.has_table("restaurantes"):
        idxs = insp.get_indexes("restaurantes")
        has_unique_email = any(ix.get("unique") and ix.get("column_names") == ["email"] for ix in idxs)
        if not has_unique_email:
            with op.batch_alter_table("restaurantes") as batch_op:
                batch_op.create_index("ix_restaurantes_email", ["email"], unique=True)


def downgrade():
    # Como a tabela pode ter sido criada fora do Alembic, faça drop com cuidado
    with op.batch_alter_table("restaurantes") as batch_op:
        try:
            batch_op.drop_index("ix_restaurantes_email")
        except Exception:
            pass
    op.drop_table("restaurantes")

