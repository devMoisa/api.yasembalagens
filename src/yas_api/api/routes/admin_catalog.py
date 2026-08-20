from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from yas_api.api.dependencies import DbSession, get_current_admin
from yas_api.models import (
    Banner,
    Category,
    Media,
    Product,
    ProductBlock,
    ProductBlockItem,
    ProductImage,
)
from yas_api.schemas.catalog import (
    BannerCreate,
    BannerRead,
    BannerUpdate,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    ProductBlockCreate,
    ProductBlockRead,
    ProductBlockUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)
from yas_api.services.slugs import slugify

router = APIRouter(dependencies=[Depends(get_current_admin)])


def get_or_404[ModelT](db: Session, model: type[ModelT], object_id: int) -> ModelT:
    instance = db.get(model, object_id)
    if instance is None:
        raise HTTPException(status_code=404, detail="Registro nao encontrado")
    return instance


def commit_or_conflict(
    db: Session, detail: str = "Dados duplicados ou referencia invalida"
) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


def update_instance(instance, payload: BaseModel) -> None:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: DbSession):
    return db.scalars(select(Category).order_by(Category.sort_order, Category.name)).all()


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: DbSession):
    values = payload.model_dump()
    values["slug"] = slugify(payload.slug or payload.name)
    category = Category(**values)
    db.add(category)
    commit_or_conflict(db)
    db.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, payload: CategoryUpdate, db: DbSession):
    category = get_or_404(db, Category, category_id)
    update_instance(category, payload)
    if payload.slug is not None:
        category.slug = slugify(payload.slug)
    commit_or_conflict(db)
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DbSession) -> Response:
    db.delete(get_or_404(db, Category, category_id))
    commit_or_conflict(db, "A categoria ainda possui produtos")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _product_query():
    return (
        select(Product)
        .options(selectinload(Product.images).selectinload(ProductImage.media))
        .order_by(Product.sort_order, Product.name)
    )


def _load_product(db: Session, product_id: int) -> Product:
    query = (
        select(Product)
        .where(Product.id == product_id)
        .options(selectinload(Product.images).selectinload(ProductImage.media))
    )
    product = db.scalar(query)
    if product is None:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
    return product


def _replace_product_images(db: Session, product: Product, media_ids: list[int]) -> None:
    if len(media_ids) != len(set(media_ids)):
        raise HTTPException(status_code=422, detail="A mesma imagem foi enviada mais de uma vez")
    if media_ids:
        existing = set(db.scalars(select(Media.id).where(Media.id.in_(media_ids))).all())
        missing = [media_id for media_id in media_ids if media_id not in existing]
        if missing:
            raise HTTPException(status_code=422, detail=f"Imagens inexistentes: {missing}")
    # Clear + flush so the DELETEs run before the new INSERTs (avoids collisions on the
    # (product_id, media_id) unique constraint when a media_id appears in both sets).
    product.images = []
    db.flush()
    product.images = [
        ProductImage(media_id=media_id, position=position)
        for position, media_id in enumerate(media_ids)
    ]


@router.get("/products", response_model=list[ProductRead])
def list_products(db: DbSession):
    return db.scalars(_product_query()).all()


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: DbSession):
    values = payload.model_dump(exclude={"image_ids"})
    values["slug"] = slugify(payload.slug or payload.name)
    product = Product(**values)
    db.add(product)
    _replace_product_images(db, product, payload.image_ids)
    commit_or_conflict(db)
    return _load_product(db, product.id)


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: DbSession):
    product = _load_product(db, product_id)
    values = payload.model_dump(exclude_unset=True, exclude={"image_ids"})
    for field, value in values.items():
        setattr(product, field, value)
    if payload.slug is not None:
        product.slug = slugify(payload.slug)
    if payload.image_ids is not None:
        _replace_product_images(db, product, payload.image_ids)
    commit_or_conflict(db)
    return _load_product(db, product.id)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: DbSession) -> Response:
    product = get_or_404(db, Product, product_id)
    # Detach gallery so the RESTRICT on product_images.media_id does not block product removal.
    product.images = []
    db.flush()
    db.delete(product)
    commit_or_conflict(db, "O produto ainda esta em uso em um bloco ou pedido")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/banners", response_model=list[BannerRead])
def list_banners(db: DbSession):
    query = select(Banner).order_by(Banner.placement, Banner.sort_order)
    return db.scalars(query).all()


@router.post("/banners", response_model=BannerRead, status_code=status.HTTP_201_CREATED)
def create_banner(payload: BannerCreate, db: DbSession):
    banner = Banner(**payload.model_dump())
    db.add(banner)
    commit_or_conflict(db)
    db.refresh(banner)
    return banner


@router.patch("/banners/{banner_id}", response_model=BannerRead)
def update_banner(banner_id: int, payload: BannerUpdate, db: DbSession):
    banner = get_or_404(db, Banner, banner_id)
    update_instance(banner, payload)
    if banner.starts_at and banner.ends_at and banner.starts_at >= banner.ends_at:
        raise HTTPException(status_code=422, detail="ends_at deve ser posterior a starts_at")
    commit_or_conflict(db)
    db.refresh(banner)
    return banner


@router.delete("/banners/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_banner(banner_id: int, db: DbSession) -> Response:
    db.delete(get_or_404(db, Banner, banner_id))
    commit_or_conflict(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def load_block(db: Session, block_id: int) -> ProductBlock:
    query = (
        select(ProductBlock)
        .where(ProductBlock.id == block_id)
        .options(
            selectinload(ProductBlock.items)
            .selectinload(ProductBlockItem.product)
            .selectinload(Product.images)
            .selectinload(ProductImage.media)
        )
    )
    block = db.scalar(query)
    if block is None:
        raise HTTPException(status_code=404, detail="Bloco nao encontrado")
    return block


def serialize_block(block: ProductBlock) -> ProductBlockRead:
    return ProductBlockRead(
        id=block.id,
        title=block.title,
        slug=block.slug,
        is_active=block.is_active,
        sort_order=block.sort_order,
        created_at=block.created_at,
        updated_at=block.updated_at,
        products=[ProductRead.model_validate(item.product) for item in block.items],
    )


def replace_block_products(db: Session, block: ProductBlock, product_ids: list[int]) -> None:
    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(status_code=422, detail="Um produto nao pode se repetir no bloco")
    existing_ids = set(db.scalars(select(Product.id).where(Product.id.in_(product_ids))).all())
    missing_ids = set(product_ids) - existing_ids
    if missing_ids:
        raise HTTPException(status_code=422, detail=f"Produtos inexistentes: {sorted(missing_ids)}")
    block.items = [
        ProductBlockItem(product_id=product_id, position=position)
        for position, product_id in enumerate(product_ids)
    ]


@router.get("/blocks", response_model=list[ProductBlockRead])
def list_blocks(db: DbSession):
    ids = db.scalars(
        select(ProductBlock.id).order_by(ProductBlock.sort_order, ProductBlock.title)
    ).all()
    return [serialize_block(load_block(db, block_id)) for block_id in ids]


@router.post("/blocks", response_model=ProductBlockRead, status_code=status.HTTP_201_CREATED)
def create_block(payload: ProductBlockCreate, db: DbSession):
    block = ProductBlock(
        title=payload.title,
        slug=slugify(payload.slug or payload.title),
        is_active=payload.is_active,
        sort_order=payload.sort_order,
    )
    db.add(block)
    replace_block_products(db, block, payload.product_ids)
    commit_or_conflict(db)
    return serialize_block(load_block(db, block.id))


@router.patch("/blocks/{block_id}", response_model=ProductBlockRead)
def update_block(block_id: int, payload: ProductBlockUpdate, db: DbSession):
    block = load_block(db, block_id)
    values = payload.model_dump(exclude_unset=True, exclude={"product_ids"})
    for field, value in values.items():
        setattr(block, field, value)
    if payload.slug is not None:
        block.slug = slugify(payload.slug)
    if payload.product_ids is not None:
        replace_block_products(db, block, payload.product_ids)
    commit_or_conflict(db)
    return serialize_block(load_block(db, block.id))


@router.delete("/blocks/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block(block_id: int, db: DbSession) -> Response:
    db.delete(get_or_404(db, ProductBlock, block_id))
    commit_or_conflict(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
