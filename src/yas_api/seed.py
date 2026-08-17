"""Carga inicial idempotente baseada na vitrine aprovada."""

from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from yas_api.core.config import settings
from yas_api.core.storage import get_storage
from yas_api.db.session import SessionLocal
from yas_api.models import (
    Banner,
    BannerPlacement,
    Category,
    ContentTone,
    Media,
    Product,
    ProductBlock,
    ProductBlockItem,
    StoreSettings,
)

CATEGORIES = [
    ("embalagens-personalizadas", "Embalagens Personalizadas", "gray", True, False, False),
    ("papelaria-personalizada", "Papelaria Personalizada", "gray", True, False, False),
    ("cupons-exclusivos", "Cupons Exclusivos até R$ 250 OFF", "brand", True, False, False),
    ("setembro-amarelo", "Setembro Amarelo", "gray", True, False, False),
    ("materiais-eleicoes", "Materiais Gráficos para Eleições 2026", "dark", True, False, False),
    ("caixas", "Caixas Personalizadas", "gray", False, True, False),
    ("sacolas", "Sacolas e Papel", "kraft", False, True, False),
    ("rotulos", "Rótulos e Etiquetas", "brand", False, True, False),
    ("delivery", "Embalagens para Delivery", "kraft", False, True, False),
    ("ecommerce", "E-commerce e Envio", "gray", False, True, False),
    ("especiais", "Linhas Especiais", "dark", False, True, False),
    ("datas", "Datas Comemorativas", "brand", False, True, True),
    ("lancamentos", "Lançamentos", "brand", False, False, False),
]

# slug, nome, preço, mínimo, prazo, categoria, tom
PRODUCTS = [
    ("caixa-sedex", "Caixa Sedex", "116.23", 250, 2, "caixas", "gray"),
    ("caixa-delivery", "Caixa Delivery", "138.90", 100, 3, "caixas", "kraft"),
    ("caixa-rigida", "Caixa Rígida", "452.80", 50, 5, "caixas", "dark"),
    ("caixa-tampa", "Caixa com Tampa", "289.50", 100, 4, "caixas", "gray"),
    ("caixa-sushi", "Caixa Sushi", "63.42", 100, 3, "caixas", "gray"),
    ("caixa-doces", "Caixa Doces", "174.60", 100, 3, "caixas", "brand"),
    ("sacola-kraft", "Sacola Kraft", "219.90", 100, 4, "sacolas", "kraft"),
    (
        "sacola-papel-fundo-largo",
        "Sacola de Papel Fundo Largo",
        "340.55",
        100,
        5,
        "sacolas",
        "kraft",
    ),
    ("papel-seda", "Papel de Seda Personalizado", "89.40", 500, 3, "sacolas", "gray"),
    ("sacola-alca-fita", "Sacola Alça Fita", "412.00", 100, 5, "sacolas", "dark"),
    ("saco-papel", "Saco de Papel", "65.90", 250, 3, "sacolas", "kraft"),
    ("envelope-seguranca", "Envelope de Segurança", "148.70", 250, 2, "sacolas", "gray"),
    ("caixa-hot-stamping", "Caixa Hot Stamping", "512.90", 50, 7, "especiais", "dark"),
    (
        "verniz-interno",
        "Embalagem com Impressão Interna em Verniz",
        "620.50",
        50,
        7,
        "especiais",
        "dark",
    ),
    ("tag-hot-stamping", "Tag Hot Stamping", "118.70", 100, 5, "especiais", "dark"),
    ("caixa-verniz-uv", "Caixa com Verniz UV", "489.90", 50, 6, "especiais", "dark"),
    ("convite-hot-stamping", "Convite Hot Stamping", "259.50", 100, 5, "especiais", "dark"),
    ("catalogo-verniz", "Catálogo Verniz", "388.40", 50, 6, "especiais", "dark"),
    ("chapeu-bucket", "Chapéu Bucket Personalizado", "340.86", 25, 6, "lancamentos", "gray"),
    ("ecobag-burgos", "Ecobag Burgos", "118.70", 50, 5, "lancamentos", "kraft"),
    ("kit-vinho", "Kit Vinho Personalizado", "218.37", 10, 7, "lancamentos", "kraft"),
    ("photocard", "Photocard Personalizado", "49.06", 100, 3, "lancamentos", "brand"),
    ("baralho-caixa", "Baralho com Caixa Personalizada", "367.84", 50, 5, "lancamentos", "dark"),
    ("sacola-fundo-largo", "Sacola de Papel Fundo Largo", "340.55", 50, 5, "lancamentos", "kraft"),
    ("adesivos-redondos", "Adesivos Redondos", "35.20", 250, 2, "rotulos", "brand"),
    (
        "pasta-personalizada",
        "Pasta Personalizada",
        "183.80",
        250,
        2,
        "papelaria-personalizada",
        "dark",
    ),
    ("folder-2-dobras", "Folder 2 Dobras", "285.84", 250, 2, "papelaria-personalizada", "gray"),
    (
        "calendario-mesa",
        "Calendário de Mesa 2027",
        "98.94",
        75,
        3,
        "papelaria-personalizada",
        "gray",
    ),
]

BLOCKS = [
    (
        "mais-vendidos",
        "Mais vendidos",
        [
            "caixa-sedex",
            "caixa-sushi",
            "adesivos-redondos",
            "pasta-personalizada",
            "folder-2-dobras",
            "calendario-mesa",
        ],
    ),
    (
        "caixas-personalizadas",
        "Caixas Personalizadas",
        [
            "caixa-sedex",
            "caixa-delivery",
            "caixa-rigida",
            "caixa-tampa",
            "caixa-sushi",
            "caixa-doces",
        ],
    ),
    (
        "sacolas-e-papel",
        "Sacolas e Papel",
        [
            "sacola-kraft",
            "sacola-papel-fundo-largo",
            "papel-seda",
            "sacola-alca-fita",
            "saco-papel",
            "envelope-seguranca",
        ],
    ),
    (
        "linhas-especiais",
        "Linhas Especiais",
        [
            "caixa-hot-stamping",
            "verniz-interno",
            "tag-hot-stamping",
            "caixa-verniz-uv",
            "convite-hot-stamping",
            "catalogo-verniz",
        ],
    ),
    (
        "lancamentos",
        "Lançamentos",
        [
            "chapeu-bucket",
            "ecobag-burgos",
            "kit-vinho",
            "photocard",
            "baralho-caixa",
            "sacola-fundo-largo",
        ],
    ),
]


def seed_database(db: Session, *, include_assets: bool = True) -> dict[str, int]:
    categories: dict[str, Category] = {}
    for order, (slug, name, tone, featured, navigation, highlighted) in enumerate(CATEGORIES):
        category = db.scalar(select(Category).where(Category.slug == slug))
        if category is None:
            category = Category(slug=slug, name=name)
            db.add(category)
        category.name = name
        category.tone = ContentTone(tone)
        category.is_featured = featured
        category.show_in_navigation = navigation
        category.is_highlighted = highlighted
        category.is_active = True
        category.sort_order = order
        categories[slug] = category
    db.flush()

    products: dict[str, Product] = {}
    for order, (slug, name, price, minimum, days, category_slug, tone) in enumerate(PRODUCTS):
        product = db.scalar(select(Product).where(Product.slug == slug))
        if product is None:
            product = Product(slug=slug, name=name, category=categories[category_slug])
            db.add(product)
        product.name = name
        product.category = categories[category_slug]
        product.price_from = Decimal(price)
        product.minimum_quantity = minimum
        product.delivery_days = days
        product.unit_label = "unidades"
        product.tone = ContentTone(tone)
        product.is_active = True
        product.sort_order = order
        products[slug] = product
    db.flush()

    for order, (slug, title, product_slugs) in enumerate(BLOCKS):
        block = db.scalar(select(ProductBlock).where(ProductBlock.slug == slug))
        if block is None:
            block = ProductBlock(slug=slug, title=title)
            db.add(block)
        block.title = title
        block.is_active = True
        block.sort_order = order
        db.flush()
        db.execute(delete(ProductBlockItem).where(ProductBlockItem.block_id == block.id))
        db.flush()
        db.add_all(
            ProductBlockItem(
                block_id=block.id,
                product_id=products[product_slug].id,
                position=position,
            )
            for position, product_slug in enumerate(product_slugs)
        )

    if include_assets:
        source = Path(__file__).with_name("seed_assets") / "hero-home.png"
        prefix = settings.spaces_key_prefix.strip("/")
        key = f"{prefix}/seed-hero-home.png" if prefix else "seed-hero-home.png"
        storage = get_storage()
        stored = storage.upload(
            key=key,
            content=source.read_bytes(),
            content_type="image/png",
        )
        media = db.scalar(select(Media).where(Media.storage_path == stored.key))
        if media is None:
            media = Media(storage_path=stored.key, public_url=stored.public_url)
            db.add(media)
        media.storage_path = stored.key
        media.public_url = stored.public_url
        media.filename = "hero-home.png"
        media.mime_type = "image/png"
        media.alt_text = "Yas Embalagens que valorizam sua marca"
        db.flush()
        banner = db.scalar(
            select(Banner).where(
                Banner.title == "Embalagens que valorizam sua marca",
                Banner.placement == BannerPlacement.HERO,
            )
        )
        if banner is None:
            banner = Banner(title="Embalagens que valorizam sua marca", image=media)
            db.add(banner)
        banner.image = media
        banner.placement = BannerPlacement.HERO
        banner.is_active = True
        banner.sort_order = 0

    if db.get(StoreSettings, 1) is None:
        db.add(StoreSettings(id=1))
    db.flush()
    return {
        "categories": len(CATEGORIES),
        "products": len(PRODUCTS),
        "blocks": len(BLOCKS),
        "banners": 1 if include_assets else 0,
    }


def main() -> None:
    with SessionLocal() as db:
        result = seed_database(db)
        db.commit()
    summary = ", ".join(f"{value} {key}" for key, value in result.items())
    print(f"Seed concluído: {summary}.")


if __name__ == "__main__":
    main()
