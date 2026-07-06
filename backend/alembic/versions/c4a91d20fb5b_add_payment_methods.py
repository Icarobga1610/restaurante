"""add payment methods

Revision ID: c4a91d20fb5b
Revises: b3f2a6d8c901
Create Date: 2026-07-06 03:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4a91d20fb5b"
down_revision: Union[str, None] = "b3f2a6d8c901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_methods",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_payment_methods_id", "payment_methods", ["id"])
    op.create_index("ix_payment_methods_code", "payment_methods", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_payment_methods_code", table_name="payment_methods")
    op.drop_index("ix_payment_methods_id", table_name="payment_methods")
    op.drop_table("payment_methods")
