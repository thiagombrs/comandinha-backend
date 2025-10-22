from alembic import op
import sqlalchemy as sa

revision = "6eaaf9c40c7d"
down_revision = "b187103d2454"
branch_labels = None
depends_on = None

def _has_column(bind, table: str, column: str) -> bool:
    insp = sa.inspect(bind)
    return any(c["name"] == column for c in insp.get_columns(table))

def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # 1) Adiciona a coluna se ainda não existir (idempotente)
    if not _has_column(bind, "produto", "disponivel"):
        op.add_column("produto", sa.Column("disponivel", sa.Boolean(), nullable=True))

    # 2) Backfill: marca todos como True
    if dialect == "postgresql":
        bind.execute(sa.text("UPDATE produto SET disponivel = TRUE WHERE disponivel IS NULL"))
    else:
        bind.execute(sa.text("UPDATE produto SET disponivel = 1 WHERE disponivel IS NULL"))

    # 3) Torna NOT NULL
    #    - PostgreSQL: pode usar alter_column direto
    #    - SQLite: use batch_alter_table (o Alembic recria a tabela por baixo dos panos)
    if dialect == "postgresql":
        op.alter_column("produto", "disponivel", existing_type=sa.Boolean(), nullable=False)
    else:
        with op.batch_alter_table("produto") as batch:
            batch.alter_column("disponivel", existing_type=sa.Boolean(), nullable=False)

def downgrade() -> None:
    with op.batch_alter_table("produto") as batch:
        batch.drop_column("disponivel")
