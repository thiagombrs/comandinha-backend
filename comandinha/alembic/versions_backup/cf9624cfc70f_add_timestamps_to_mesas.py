"""add timestamps to mesas

Revision ID: cf9624cfc70f
Revises: 6eaaf9c40c7d
Create Date: 2025-09-11 13:30:15.880912

"""
# versions/<stamp>_add_timestamps_to_mesas.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

revision = "cf9624cfc70f"
down_revision = "6eaaf9c40c7d"
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona as colunas só se NÃO existirem (PostgreSQL)
    op.execute("""
        ALTER TABLE mesa
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;
    """)
    op.execute("""
        ALTER TABLE mesa
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ;
    """)

    # (opcional) garantir defaults/NOT NULL sem quebrar dados existentes:
    # Preenche nulos com now()
    op.execute("""
        UPDATE mesa
        SET created_at = COALESCE(created_at, NOW()),
            updated_at = COALESCE(updated_at, NOW());
    """)
    # Define default para novas linhas
    op.execute("""
        ALTER TABLE mesa
        ALTER COLUMN created_at SET DEFAULT NOW(),
        ALTER COLUMN updated_at SET DEFAULT NOW();
    """)
    # (se você quiser NOT NULL, descomente)
    # op.execute("""
    #     ALTER TABLE mesa
    #     ALTER COLUMN created_at SET NOT NULL,
    #     ALTER COLUMN updated_at SET NOT NULL;
    # """)

def downgrade():
    # Remover colunas só se existirem (PostgreSQL)
    op.execute("""
        ALTER TABLE mesa
        DROP COLUMN IF EXISTS updated_at;
    """)
    op.execute("""
        ALTER TABLE mesa
        DROP COLUMN IF EXISTS created_at;
    """)