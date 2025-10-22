"""add mesa_status to mesa

Revision ID: abc6c8c869b2
Revises: cf9624cfc70f
Create Date: 2025-09-11 17:49:42.766097

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc6c8c869b2'
down_revision: Union[str, None] = 'cf9624cfc70f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) adiciona como NULL (sem default do servidor)
    with op.batch_alter_table("mesa") as batch_op:
        batch_op.add_column(sa.Column("mesa_status", sa.Integer(), nullable=True))

    # 2) preenche registros existentes com 1 (disponivel)
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE mesa SET mesa_status = 1 WHERE mesa_status IS NULL"))

    # 3) torna NOT NULL
    with op.batch_alter_table("mesa") as batch_op:
        batch_op.alter_column("mesa_status", existing_type=sa.Integer(), nullable=False)

def downgrade():
    with op.batch_alter_table("mesa") as batch_op:
        batch_op.drop_column("mesa_status")