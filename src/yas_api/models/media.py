from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from yas_api.db.base import Base, TimestampMixin


class Media(TimestampMixin, Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500), unique=True)
    public_url: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    alt_text: Mapped[str | None] = mapped_column(String(255))
