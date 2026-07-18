"""add operational codes to orders, products and stock items

Revision ID: 7d4b8f2a1c90
Revises: 2e7c1a4b9d10
"""

from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa

revision: str = "7d4b8f2a1c90"
down_revision: Union[str, None] = "2e7c1a4b9d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _backfill_codes(table: str, prefix: str) -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text(f"SELECT id FROM {table} WHERE code IS NULL ORDER BY id")).fetchall()
    for row in rows:
        bind.execute(
            sa.text(f"UPDATE {table} SET code = :code WHERE id = :id"),
            {"code": f"{prefix}-{row.id:06d}", "id": row.id},
        )


def upgrade() -> None:
    op.add_column("products", sa.Column("code", sa.String(length=20), nullable=True))
    op.add_column("orders", sa.Column("code", sa.String(length=20), nullable=True))
    op.add_column("stock_items", sa.Column("code", sa.String(length=20), nullable=True))

    if not context.is_offline_mode():
        _backfill_codes("products", "PRD")
        _backfill_codes("orders", "PED")
        _backfill_codes("stock_items", "ING")

    op.create_index("ix_products_code", "products", ["code"], unique=True)
    op.create_index("ix_orders_code", "orders", ["code"], unique=True)
    op.create_index("ix_stock_items_code", "stock_items", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_stock_items_code", table_name="stock_items")
    op.drop_index("ix_orders_code", table_name="orders")
    op.drop_index("ix_products_code", table_name="products")
    op.drop_column("stock_items", "code")
    op.drop_column("orders", "code")
    op.drop_column("products", "code")
