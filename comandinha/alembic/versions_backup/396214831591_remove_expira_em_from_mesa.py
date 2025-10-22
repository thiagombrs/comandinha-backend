"""remove expira_em from mesa

Revision ID: 396214831591
Revises: 440d1e9b6b1c
Create Date: 2025-09-15 13:29:10.419401

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '396214831591'
down_revision: Union[str, None] = '440d1e9b6b1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    with op.batch_alter_table('mesa') as batch_op:
        batch_op.drop_column('expira_em')

def downgrade():
    with op.batch_alter_table('mesa') as batch_op:
        batch_op.add_column(
            sa.Column('expira_em', sa.DateTime(), nullable=True)
        )