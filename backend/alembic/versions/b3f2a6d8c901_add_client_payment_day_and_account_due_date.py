"""add client payment day and account due date

Revision ID: b3f2a6d8c901
Revises: 9b0bf3bd360d
Create Date: 2026-07-06 02:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3f2a6d8c901"
down_revision: Union[str, None] = "9b0bf3bd360d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("payment_day", sa.Integer(), nullable=True))
    op.add_column("monthly_accounts", sa.Column("due_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("monthly_accounts", "due_date")
    op.drop_column("clients", "payment_day")
