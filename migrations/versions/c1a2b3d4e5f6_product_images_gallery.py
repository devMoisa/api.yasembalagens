"""product images gallery

Revision ID: c1a2b3d4e5f6
Revises: 8f4e2d0c97a1
Create Date: 2026-08-19 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c1a2b3d4e5f6"
down_revision: str | Sequence[str] | None = "8f4e2d0c97a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_images",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("product_id", "media_id", name="uq_product_images_product_media"),
    )
    op.create_index(
        "ix_product_images_product_position",
        "product_images",
        ["product_id", "position"],
    )

    # Backfill from products.image_id
    op.execute(
        """
        INSERT INTO product_images (product_id, media_id, position)
        SELECT id, image_id, 0 FROM products WHERE image_id IS NOT NULL
        """
    )

    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_column("image_id")


def downgrade() -> None:
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(sa.Column("image_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_products_image_id",
            "media",
            ["image_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        """
        UPDATE products
        SET image_id = (
            SELECT media_id FROM product_images
            WHERE product_images.product_id = products.id
            ORDER BY position ASC, id ASC
            LIMIT 1
        )
        """
    )

    op.drop_index("ix_product_images_product_position", table_name="product_images")
    op.drop_table("product_images")
