"""add status_id to pedido (1=pending,2=preparo,3=entregue,4=concluido)

Revision ID: a879fdb50458
Revises: c448ed7ed774
Create Date: 2025-09-12 13:26:12.502885

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a879fdb50458'
down_revision: Union[str, None] = 'c448ed7ed774'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
