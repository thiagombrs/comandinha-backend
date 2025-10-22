"""drop token/expira_em from mesa; enforce mesa_status

Revision ID: cbfe45962ebe
Revises: 396214831591
Create Date: 2025-09-15 14:53:25.548579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbfe45962ebe'
down_revision: Union[str, None] = '396214831591'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # colunas e índices existentes hoje
    cols = {c["name"] for c in insp.get_columns("mesa")}
    idxs = {i["name"] for i in insp.get_indexes("mesa")}

    # Faça o batch normalmente (o Alembic vai recriar a mesa no SQLite)
    with op.batch_alter_table("mesa") as batch_op:
        # dropar índices relacionados ao token, se houver
        if "ix_mesa_token" in idxs:
            try:
                batch_op.drop_index("ix_mesa_token")
            except Exception:
                pass  # ignorar se não existir no contexto do batch

        # dropar colunas antigas, se existirem
        if "token" in cols:
            batch_op.drop_column("token")
        if "expira_em" in cols:
            batch_op.drop_column("expira_em")

        # garantir mesa_status presente e não nulo com default 1
        if "mesa_status" not in cols:
            batch_op.add_column(
                sa.Column("mesa_status", sa.Integer(), nullable=False, server_default=sa.text("1"))
            )
        else:
            batch_op.alter_column(
                "mesa_status",
                existing_type=sa.Integer(),
                nullable=False,
                server_default=sa.text("1"),
            )
