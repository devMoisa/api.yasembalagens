from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from yas_api.db.base import Base, TimestampMixin
from yas_api.models.media import Media


class ContentTone(StrEnum):
    GRAY = "gray"
    BRAND = "brand"
    DARK = "dark"
    KRAFT = "kraft"


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    image_id: Mapped[int | None] = mapped_column(ForeignKey("media.id", ondelete="SET NULL"))
    tone: Mapped[ContentTone] = mapped_column(
        Enum(ContentTone, native_enum=False, length=20),
        default=ContentTone.GRAY,
        server_default="GRAY",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    show_in_navigation: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    is_highlighted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    image: Mapped[Media | None] = relationship()
    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(180))
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    sku: Mapped[str | None] = mapped_column(String(80), unique=True)
    short_description: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    price_from: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    unit_label: Mapped[str] = mapped_column(String(80), default="unidade")
    minimum_quantity: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    delivery_days: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    image_id: Mapped[int | None] = mapped_column(ForeignKey("media.id", ondelete="SET NULL"))
    tone: Mapped[ContentTone] = mapped_column(
        Enum(ContentTone, native_enum=False, length=20),
        default=ContentTone.GRAY,
        server_default="GRAY",
    )
    badge_text: Mapped[str | None] = mapped_column(String(80))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    category: Mapped[Category] = relationship(back_populates="products")
    image: Mapped[Media | None] = relationship()


class ProductBlock(TimestampMixin, Base):
    __tablename__ = "product_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    items: Mapped[list["ProductBlockItem"]] = relationship(
        back_populates="block", cascade="all, delete-orphan", order_by="ProductBlockItem.position"
    )


class ProductBlockItem(Base):
    __tablename__ = "product_block_items"
    __table_args__ = (UniqueConstraint("block_id", "product_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    block_id: Mapped[int] = mapped_column(ForeignKey("product_blocks.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    block: Mapped[ProductBlock] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()
