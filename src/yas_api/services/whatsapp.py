from decimal import Decimal
from urllib.parse import quote

from yas_api.models import Product, StoreSettings


def format_brl(value: Decimal) -> str:
    formatted = f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"


def build_quote(
    store_settings: StoreSettings,
    customer_name: str,
    customer_whatsapp: str,
    requested_items: list[tuple[Product, int]],
) -> tuple[str, str | None, str | None, Decimal | None]:
    item_lines: list[str] = []
    total = Decimal("0")
    has_complete_total = True

    for product, package_count in requested_items:
        quantity = product.minimum_quantity * package_count
        line = f"- {product.name}: {quantity} {product.unit_label}"
        if package_count > 1:
            line += f" ({package_count} pacotes)"
        if product.price_from is not None:
            subtotal = product.price_from * package_count
            total += subtotal
            line += f" (a partir de {format_brl(subtotal)})"
        else:
            has_complete_total = False
        item_lines.append(line)

    estimated_total = total if has_complete_total else None
    total_text = format_brl(total) if has_complete_total else "a confirmar"
    template_has_customer_whatsapp = "{customer_whatsapp}" in (
        store_settings.whatsapp_message_template
    )
    message = (
        store_settings.whatsapp_message_template.replace("{items}", "\n".join(item_lines))
        .replace("{total}", total_text)
        .replace("{customer_name}", customer_name)
        .replace("{customer_whatsapp}", customer_whatsapp)
    )
    if not template_has_customer_whatsapp:
        message += f"\n\nWhatsApp do cliente: {customer_whatsapp}"
    whatsapp_url = None
    if store_settings.whatsapp_phone:
        whatsapp_url = (
            f"https://wa.me/{store_settings.whatsapp_phone}?text={quote(message, safe='')}"
        )

    email_url = None
    if store_settings.order_email:
        subject = store_settings.order_email_subject.replace("{customer_name}", customer_name)
        email_url = (
            f"mailto:{store_settings.order_email}?subject={quote(subject, safe='')}"
            f"&body={quote(message, safe='')}"
        )

    return message, whatsapp_url, email_url, estimated_total
