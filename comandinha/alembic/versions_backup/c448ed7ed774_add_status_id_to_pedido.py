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
    # Adiciona a coluna apenas se NÃO existir
    op.execute("""
        ALTER TABLE pedido
        ADD COLUMN IF NOT EXISTS status_id INTEGER
    """)

    # (opcional) se você tem FK para uma tabela 'status' ou algo assim, crie a constraint só se não existir
    # Exemplo genérico (ajuste nomes da FK/tabela/coluna de referência):
    # op.execute("""
    #     DO $$
    #     BEGIN
    #         IF NOT EXISTS (
    #             SELECT 1 FROM pg_constraint
    #             WHERE conname = 'fk_pedido_status'
    #         ) THEN
    #             ALTER TABLE pedido
    #             ADD CONSTRAINT fk_pedido_status
    #             FOREIGN KEY (status_id) REFERENCES status(id);
    #         END IF;
    #     END
    #     $$;
    # """)

def downgrade():
    # Remove a coluna apenas se existir
    op.execute("""
        ALTER TABLE pedido
        DROP COLUMN IF EXISTS status_id
    """)
