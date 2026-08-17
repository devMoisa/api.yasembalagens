from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from yas_api.db.base import Base, TimestampMixin


class StoreSettings(TimestampMixin, Base):
    __tablename__ = "store_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    store_name: Mapped[str] = mapped_column(String(160), default="Yas Embalagens")
    whatsapp_phone: Mapped[str] = mapped_column(String(20), default="")
    order_email: Mapped[str] = mapped_column(String(255), default="")
    order_email_subject: Mapped[str] = mapped_column(
        String(180), default="Novo pedido de orçamento - {customer_name}"
    )
    whatsapp_message_template: Mapped[str] = mapped_column(
        Text,
        default=(
            "Ola! Gostaria de solicitar um orcamento:\n\n{items}\n\n"
            "Total estimado: {total}\n\nNome: {customer_name}\n"
            "WhatsApp: {customer_whatsapp}"
        ),
    )
    show_prices: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
