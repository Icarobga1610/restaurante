"""Resolve missing alembic history head issue."""

from alembic import op
import sqlalchemy as sa


revision = "7af7c8bad3d6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alembic_version",
        sa.Column("version_num", sa.String(32), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("alembic_version")
