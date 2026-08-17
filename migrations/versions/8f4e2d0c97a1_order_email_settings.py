"""order email settings

Revision ID: 8f4e2d0c97a1
Revises: b53eba3c2fec
Create Date: 2026-08-10 22:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8f4e2d0c97a1"
down_revision: str | Sequence[str] | None = "b53eba3c2fec"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("store_settings", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("order_email", sa.String(length=255), server_default="", nullable=False)
        )
        batch_op.add_column(
            sa.Column(
                "order_email_subject",
                sa.String(length=180),
                server_default="Novo pedido de orçamento - {customer_name}",
                nullable=False,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("store_settings", schema=None) as batch_op:
        batch_op.drop_column("order_email_subject")
        batch_op.drop_column("order_email")
