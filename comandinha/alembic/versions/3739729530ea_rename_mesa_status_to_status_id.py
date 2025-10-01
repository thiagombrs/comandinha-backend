"""rename mesa_status to status_id

Revision ID: 3739729530ea
Revises: 3c4bca9692d9
Create Date: 2025-09-29 16:57:18.404835

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3739729530ea'
down_revision: Union[str, None] = '3c4bca9692d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # Para SQLite, use batch_alter_table para preservar dados/índices/constraints
        with op.batch_alter_table("mesa", schema=None) as batch_op:
            batch_op.alter_column(
                "mesa_status",
                new_column_name="status_id",
                existing_type=sa.Integer(),
                existing_nullable=False,
                existing_server_default=sa.text("1"),
            )
    else:
        # Em outros dialetos, o rename direto funciona
        op.alter_column(
            "mesa",
            "mesa_status",
            new_column_name="status_id",
            existing_type=sa.Integer(),
            existing_nullable=False,
            existing_server_default=sa.text("1"),
        )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("mesa", schema=None) as batch_op:
            batch_op.alter_column(
                "status_id",
                new_column_name="mesa_status",
                existing_type=sa.Integer(),
                existing_nullable=False,
                existing_server_default=sa.text("1"),
            )
    else:
        op.alter_column(
            "mesa",
            "status_id",
            new_column_name="mesa_status",
            existing_type=sa.Integer(),
            existing_nullable=False,
            existing_server_default=sa.text("1"),
        )