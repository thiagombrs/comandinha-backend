"""add status_id to pedido

Revision ID: c448ed7ed774
Revises: abc6c8c869b2
Create Date: 2025-09-12 13:11:25.403696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c448ed7ed774'
down_revision: Union[str, None] = 'abc6c8c869b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) adiciona a coluna permitindo NULL (compatível com SQLite)
    with op.batch_alter_table("pedido") as batch_op:  # se sua tabela for "pedidos", troque o nome aqui e abaixo
        batch_op.add_column(sa.Column("status_id", sa.Integer(), nullable=True))

    # 2) backfill a partir de 'status' textual que você já usa hoje
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE pedido
        SET status_id = CASE
            WHEN status IN ('pendente','confirmado') THEN 1
            WHEN status IN ('em_preparo','preparando') THEN 2
            WHEN status = 'entregue' THEN 3
            WHEN status = 'concluido' THEN 4
            ELSE 1
        END
        WHERE status_id IS NULL
    """))

    # 3) travar NOT NULL + default constante e CHECK 1..4
    with op.batch_alter_table("pedido") as batch_op:
        batch_op.alter_column(
            "status_id",
            existing_type=sa.Integer(),
            nullable=False,
            server_default="1",
        )
        batch_op.create_check_constraint(
            "ck_pedido_status_id_range",
            "status_id IN (1,2,3,4)"
        )

    # 4) índice útil
    op.create_index("ix_pedido_status_id", "pedido", ["status_id"], unique=False)


def downgrade():
    op.drop_index("ix_pedido_status_id", table_name="pedido")
    with op.batch_alter_table("pedido") as batch_op:
        try:
            batch_op.drop_constraint("ck_pedido_status_id_range", type_="check")
        except Exception:
            pass
        batch_op.drop_column("status_id")
