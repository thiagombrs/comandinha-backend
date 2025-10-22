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
    # Remover QUALQUER check constraint anterior em status_id (nome pode variar)
    op.execute("""
    DO $$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN
            SELECT conname
            FROM   pg_constraint c
            JOIN   pg_class t   ON t.oid = c.conrelid
            JOIN   pg_namespace n ON n.oid = t.relnamespace
            WHERE  t.relname = 'pedido'
            AND    c.contype = 'c'          -- CHECK
            AND    pg_get_constraintdef(c.oid) ILIKE '%status_id%'
        LOOP
            EXECUTE format('ALTER TABLE pedido DROP CONSTRAINT %I', r.conname);
        END LOOP;
    END
    $$;
    """)

    # Criar a NOVA check constraint (1..4)
    op.execute("""
        ALTER TABLE pedido
        ADD CONSTRAINT ck_pedido_status_id_range
        CHECK (status_id BETWEEN 1 AND 4)
    """)

def downgrade():

    op.execute("""
        ALTER TABLE pedido
        DROP CONSTRAINT IF EXISTS ck_pedido_status_id_range
    """)
    op.execute("""
        ALTER TABLE pedido
        ADD CONSTRAINT ck_pedido_status_id_range
        CHECK (status_id IN (1,2,3))   -- exemplo; ajuste para o que era antes, se necessário
    """)