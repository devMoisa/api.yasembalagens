from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from yas_api.db.base import Base, TimestampMixin
from yas_api.models.media import Media


class BannerPlacement(StrEnum):
    HERO = "hero"
    MIDDLE = "middle"
    FOOTER = "footer"


class Banner(TimestampMixin, Base):
    __tablename__ = "banners"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(180))
    subtitle: Mapped[str | None] = mapped_column(Text)
    placement: Mapped[BannerPlacement] = mapped_column(
        Enum(BannerPlacement, native_enum=False, length=20), default=BannerPlacement.HERO
    )
    image_id: Mapped[int] = mapped_column(ForeignKey("media.id", ondelete="RESTRICT"))
    mobile_image_id: Mapped[int | None] = mapped_column(ForeignKey("media.id", ondelete="SET NULL"))
    button_label: Mapped[str | None] = mapped_column(String(80))
    link_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    image: Mapped[Media] = relationship(foreign_keys=[image_id])
    mobile_image: Mapped[Media | None] = relationship(foreign_keys=[mobile_image_id])
