"""force drop mesa.token (sqlite recreate)

Revision ID: 3c4bca9692d9
Revises: cbfe45962ebe
Create Date: 2025-09-21 17:06:50.547636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c4bca9692d9'
down_revision: Union[str, None] = 'cbfe45962ebe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("mesa")}

    # Só entra no batch se houver algo a fazer
    need_recreate = (
        "token" in cols
        or "expira_em" in cols
        or "mesa_status" not in cols
    )

    if not need_recreate:
        # Mesmo assim, reforça NOT NULL e default da mesa_status, se necessário
        with op.batch_alter_table("mesa", recreate="always") as batch_op:
            batch_op.alter_column(
                "mesa_status",
                existing_type=sa.Integer(),
                nullable=False,
                server_default=sa.text("1"),
            )
        return

    with op.batch_alter_table("mesa", recreate="always") as batch_op:
        # remover colunas legadas, se existirem
        if "token" in cols:
            batch_op.drop_column("token")
        if "expira_em" in cols:
            batch_op.drop_column("expira_em")

        # garantir mesa_status presente e coerente
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


def downgrade():
    # Traz de volta as colunas legadas (se realmente precisar fazer downgrade)
    with op.batch_alter_table("mesa", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("token", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("expira_em", sa.DateTime(), nullable=True))
        batch_op.alter_column(
            "mesa_status",
            existing_type=sa.Integer(),
            nullable=True,
            server_default=None,
        )