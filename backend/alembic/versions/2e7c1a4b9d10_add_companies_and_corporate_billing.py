"""add companies and corporate monthly billing

Revision ID: 2e7c1a4b9d10
Revises: c4a91d20fb5b
Create Date: 2026-07-18 23:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2e7c1a4b9d10"
down_revision: Union[str, None] = "c4a91d20fb5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("legal_name", sa.String(length=200), nullable=False),
        sa.Column("trade_name", sa.String(length=150), nullable=True),
        sa.Column("document", sa.String(length=20), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("monthly_limit", sa.Float(), nullable=True),
        sa.Column("payment_day", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_companies_id", "companies", ["id"])
    op.create_index("ix_companies_legal_name", "companies", ["legal_name"])
    op.create_index("ix_companies_trade_name", "companies", ["trade_name"])
    op.create_index("ix_companies_document", "companies", ["document"], unique=True)
    op.create_index("ix_companies_status", "companies", ["status"])
    op.add_column("clients", sa.Column("company_id", sa.Integer(), nullable=True))
    op.create_index("ix_clients_company_id", "clients", ["company_id"])
    op.create_foreign_key("fk_clients_company_id", "clients", "companies", ["company_id"], ["id"])

    op.create_table(
        "company_monthly_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("total", sa.Float(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("closed_by", sa.Integer(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("paid_by", sa.Integer(), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("over_limit", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["closed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["paid_by"], ["users.id"]),
    )
    op.create_index("ix_company_monthly_accounts_id", "company_monthly_accounts", ["id"])
    op.create_index("ix_company_monthly_accounts_company_id", "company_monthly_accounts", ["company_id"])
    op.create_index("ix_company_monthly_accounts_status", "company_monthly_accounts", ["status"])
    op.create_index(
        "uq_company_monthly_accounts_period",
        "company_monthly_accounts",
        ["company_id", "month", "year"],
        unique=True,
    )

    op.create_table(
        "company_monthly_account_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_monthly_account_id", sa.Integer(), nullable=False),
        sa.Column("monthly_account_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("client_total", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_monthly_account_id"], ["company_monthly_accounts.id"]),
        sa.ForeignKeyConstraint(["monthly_account_id"], ["monthly_accounts.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
    )
    op.create_index("ix_company_monthly_account_items_id", "company_monthly_account_items", ["id"])

    op.create_table(
        "company_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_monthly_account_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_monthly_account_id"], ["company_monthly_accounts.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_company_payments_id", "company_payments", ["id"])
    op.create_index("ix_company_payments_company_id", "company_payments", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_company_payments_company_id", table_name="company_payments")
    op.drop_index("ix_company_payments_id", table_name="company_payments")
    op.drop_table("company_payments")
    op.drop_index("ix_company_monthly_account_items_id", table_name="company_monthly_account_items")
    op.drop_table("company_monthly_account_items")
    op.drop_index("uq_company_monthly_accounts_period", table_name="company_monthly_accounts")
    op.drop_index("ix_company_monthly_accounts_status", table_name="company_monthly_accounts")
    op.drop_index("ix_company_monthly_accounts_company_id", table_name="company_monthly_accounts")
    op.drop_index("ix_company_monthly_accounts_id", table_name="company_monthly_accounts")
    op.drop_table("company_monthly_accounts")
    op.drop_constraint("fk_clients_company_id", "clients", type_="foreignkey")
    op.drop_index("ix_clients_company_id", table_name="clients")
    op.drop_column("clients", "company_id")
    op.drop_index("ix_companies_status", table_name="companies")
    op.drop_index("ix_companies_document", table_name="companies")
    op.drop_index("ix_companies_trade_name", table_name="companies")
    op.drop_index("ix_companies_legal_name", table_name="companies")
    op.drop_index("ix_companies_id", table_name="companies")
    op.drop_table("companies")
