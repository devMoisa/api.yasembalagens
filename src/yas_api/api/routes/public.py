from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from yas_api.api.dependencies import DbSession
from yas_api.models import Banner, Category, Product, ProductBlock, ProductBlockItem
from yas_api.schemas.catalog import (
    BannerRead,
    CategoryRead,
    ProductBlockRead,
    ProductRead,
    QuoteRequest,
    QuoteResponse,
    StorefrontRead,
)
from yas_api.services.settings import get_or_create_store_settings
from yas_api.services.whatsapp import build_quote

router = APIRouter(prefix="/public", tags=["Vitrine publica"])


def serialize_block(block: ProductBlock) -> ProductBlockRead:
    return ProductBlockRead(
        id=block.id,
        title=block.title,
        slug=block.slug,
        is_active=block.is_active,
        sort_order=block.sort_order,
        created_at=block.created_at,
        updated_at=block.updated_at,
        products=[
            ProductRead.model_validate(item.product)
            for item in block.items
            if item.product.is_active
        ],
    )


@router.get("/storefront", response_model=StorefrontRead)
def storefront(db: DbSession) -> StorefrontRead:
    now = datetime.now(UTC)
    banner_query = (
        select(Banner)
        .where(
            Banner.is_active.is_(True),
            or_(Banner.starts_at.is_(None), Banner.starts_at <= now),
            or_(Banner.ends_at.is_(None), Banner.ends_at > now),
        )
        .order_by(Banner.placement, Banner.sort_order)
    )
    category_query = (
        select(Category)
        .where(Category.is_active.is_(True))
        .options(selectinload(Category.image))
        .order_by(Category.sort_order, Category.name)
    )
    block_query = (
        select(ProductBlock)
        .where(ProductBlock.is_active.is_(True))
        .options(
            selectinload(ProductBlock.items)
            .selectinload(ProductBlockItem.product)
            .selectinload(Product.image)
        )
        .order_by(ProductBlock.sort_order, ProductBlock.title)
    )
    banners = db.scalars(banner_query).all()
    categories = db.scalars(category_query).all()
    blocks = db.scalars(block_query).all()
    return StorefrontRead(
        settings=get_or_create_store_settings(db),
        banners=[BannerRead.model_validate(banner) for banner in banners],
        categories=[CategoryRead.model_validate(category) for category in categories],
        blocks=[serialize_block(block) for block in blocks],
    )


@router.get("/products", response_model=list[ProductRead])
def products(
    db: DbSession,
    category: str | None = None,
    search: str | None = Query(default=None, min_length=2, max_length=100),
):
    query = select(Product).where(Product.is_active.is_(True)).options(selectinload(Product.image))
    if category:
        query = query.join(Product.category).where(Category.slug == category)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    return db.scalars(query.order_by(Product.sort_order, Product.name)).all()


@router.get("/products/{slug}", response_model=ProductRead)
def product_detail(slug: str, db: DbSession):
    query = (
        select(Product)
        .where(Product.slug == slug, Product.is_active.is_(True))
        .options(selectinload(Product.image))
    )
    product = db.scalar(query)
    if product is None:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
    return product


@router.post("/quote", response_model=QuoteResponse)
def quote_request(payload: QuoteRequest, db: DbSession) -> QuoteResponse:
    settings = get_or_create_store_settings(db)
    if not settings.whatsapp_phone and not settings.order_email:
        raise HTTPException(status_code=503, detail="Destino dos pedidos ainda nao configurado")

    product_ids = [item.product_id for item in payload.items]
    products_by_id = {
        product.id: product
        for product in db.scalars(
            select(Product).where(Product.id.in_(product_ids), Product.is_active.is_(True))
        ).all()
    }
    missing_ids = set(product_ids) - products_by_id.keys()
    if missing_ids:
        raise HTTPException(
            status_code=422, detail=f"Produtos indisponiveis: {sorted(missing_ids)}"
        )

    requested_items = []
    for item in payload.items:
        product = products_by_id[item.product_id]
        requested_items.append((product, item.package_count))

    message, whatsapp_url, email_url, estimated_total = build_quote(
        settings,
        payload.customer_name,
        payload.customer_whatsapp,
        requested_items,
    )
    return QuoteResponse(
        message=message,
        whatsapp_url=whatsapp_url,
        email_url=email_url,
        estimated_total=estimated_total,
    )
