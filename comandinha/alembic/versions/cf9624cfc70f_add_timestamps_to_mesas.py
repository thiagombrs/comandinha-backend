"""add timestamps to mesas

Revision ID: cf9624cfc70f
Revises: 6eaaf9c40c7d
Create Date: 2025-09-11 13:30:15.880912

"""
# versions/<stamp>_add_timestamps_to_mesas.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = "cf9624cfc70f"
down_revision = "6eaaf9c40c7d"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    # 1) adiciona colunas como NULL (sem default do servidor)
    with op.batch_alter_table("mesa") as batch_op:
        batch_op.add_column(sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    # 2) preenche valores atuais com timestamp do SQLite
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE mesa SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
    conn.execute(sa.text("UPDATE mesa SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"))

    # 3) opcional: marca como NOT NULL (batch_alter recria a tabela no SQLite)
    with op.batch_alter_table("mesa") as batch_op:
        batch_op.alter_column("created_at", existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.alter_column("updated_at", existing_type=sa.DateTime(timezone=True), nullable=False)

def downgrade():
    with op.batch_alter_table("mesa") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")

