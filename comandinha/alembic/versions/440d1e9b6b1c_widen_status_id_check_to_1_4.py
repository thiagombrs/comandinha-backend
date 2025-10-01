"""widen status_id check to 1..4

Revision ID: 440d1e9b6b1c
Revises: a879fdb50458
Create Date: 2025-09-13 17:51:34.857854

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '440d1e9b6b1c'
down_revision: Union[str, None] = 'a879fdb50458'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Em SQLite, alterações em CHECK exigem recriação da tabela.
    # O batch_alter_table com recreate="always" cuida de copiar dados/índices e recriar o CHECK.
    with op.batch_alter_table("pedido", recreate="always") as batch_op:
        # Se o CHECK existir, removemos pelo nome conhecido
        batch_op.drop_constraint("ck_pedido_status_id_range", type_="check")
        # Criamos o novo CHECK permitindo 1..4
        batch_op.create_check_constraint(
            "ck_pedido_status_id_range",
            "status_id IN (1,2,3,4)"
        )


def downgrade():
    with op.batch_alter_table("pedido", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_pedido_status_id_range", type_="check")
        batch_op.create_check_constraint(
            "ck_pedido_status_id_range",
            "status_id IN (1,2,3)"
        )
