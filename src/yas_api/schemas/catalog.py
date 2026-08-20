from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from yas_api.models.banner import BannerPlacement
from yas_api.models.catalog import ContentTone
from yas_api.schemas.common import Timestamped
from yas_api.schemas.media import MediaRead


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    description: str | None = None
    image_id: int | None = None
    tone: ContentTone = ContentTone.GRAY
    is_active: bool = True
    is_featured: bool = False
    show_in_navigation: bool = True
    is_highlighted: bool = False
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, min_length=1, max_length=140)
    description: str | None = None
    image_id: int | None = None
    tone: ContentTone | None = None
    is_active: bool | None = None
    is_featured: bool | None = None
    show_in_navigation: bool | None = None
    is_highlighted: bool | None = None
    sort_order: int | None = None


class CategoryRead(Timestamped):
    name: str
    slug: str
    description: str | None
    image_id: int | None
    image: MediaRead | None
    tone: ContentTone
    is_active: bool
    is_featured: bool
    show_in_navigation: bool
    is_highlighted: bool
    sort_order: int


class ProductImageRead(BaseModel):
    id: int
    media_id: int
    position: int
    media: MediaRead

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=180)
    slug: str | None = Field(default=None, max_length=200)
    sku: str | None = Field(default=None, max_length=80)
    short_description: str | None = Field(default=None, max_length=500)
    description: str | None = None
    price_from: Decimal | None = Field(default=None, ge=0)
    unit_label: str = Field(default="unidade", min_length=1, max_length=80)
    minimum_quantity: int = Field(default=1, ge=1)
    delivery_days: int = Field(default=3, ge=1, le=365)
    image_ids: list[int] = Field(default_factory=list)
    tone: ContentTone = ContentTone.GRAY
    badge_text: str | None = Field(default=None, max_length=80)
    is_active: bool = True
    is_featured: bool = False
    sort_order: int = 0


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=180)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    sku: str | None = Field(default=None, max_length=80)
    short_description: str | None = Field(default=None, max_length=500)
    description: str | None = None
    price_from: Decimal | None = Field(default=None, ge=0)
    unit_label: str | None = Field(default=None, min_length=1, max_length=80)
    minimum_quantity: int | None = Field(default=None, ge=1)
    delivery_days: int | None = Field(default=None, ge=1, le=365)
    image_ids: list[int] | None = None
    tone: ContentTone | None = None
    badge_text: str | None = Field(default=None, max_length=80)
    is_active: bool | None = None
    is_featured: bool | None = None
    sort_order: int | None = None


class ProductRead(Timestamped):
    category_id: int
    name: str
    slug: str
    sku: str | None
    short_description: str | None
    description: str | None
    price_from: Decimal | None
    unit_label: str
    minimum_quantity: int
    delivery_days: int
    image_id: int | None
    image: MediaRead | None
    images: list[ProductImageRead]
    tone: ContentTone
    badge_text: str | None
    is_active: bool
    is_featured: bool
    sort_order: int


class BannerCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    subtitle: str | None = None
    placement: BannerPlacement = BannerPlacement.HERO
    image_id: int
    mobile_image_id: int | None = None
    button_label: str | None = Field(default=None, max_length=80)
    link_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True
    sort_order: int = 0
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @model_validator(mode="after")
    def validate_period(self):
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValueError("ends_at deve ser posterior a starts_at")
        return self


class BannerUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=180)
    subtitle: str | None = None
    placement: BannerPlacement | None = None
    image_id: int | None = None
    mobile_image_id: int | None = None
    button_label: str | None = Field(default=None, max_length=80)
    link_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None
    sort_order: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class BannerRead(Timestamped):
    title: str
    subtitle: str | None
    placement: BannerPlacement
    image_id: int
    image: MediaRead
    mobile_image_id: int | None
    mobile_image: MediaRead | None
    button_label: str | None
    link_url: str | None
    is_active: bool
    sort_order: int
    starts_at: datetime | None
    ends_at: datetime | None


class ProductBlockCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    product_ids: list[int] = Field(default_factory=list)
    is_active: bool = True
    sort_order: int = 0


class ProductBlockUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, min_length=1, max_length=140)
    product_ids: list[int] | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class ProductBlockRead(Timestamped):
    title: str
    slug: str
    is_active: bool
    sort_order: int
    products: list[ProductRead]


class StoreSettingsRead(Timestamped):
    store_name: str
    whatsapp_phone: str
    order_email: str
    order_email_subject: str
    whatsapp_message_template: str
    show_prices: bool


class StoreSettingsUpdate(BaseModel):
    store_name: str | None = Field(default=None, min_length=1, max_length=160)
    whatsapp_phone: str | None = Field(default=None, pattern=r"^\d{0,20}$")
    order_email: str | None = Field(
        default=None,
        max_length=255,
        pattern=r"^$|^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    order_email_subject: str | None = Field(default=None, min_length=1, max_length=180)
    whatsapp_message_template: str | None = None
    show_prices: bool | None = None


class StorefrontRead(BaseModel):
    settings: StoreSettingsRead
    banners: list[BannerRead]
    categories: list[CategoryRead]
    blocks: list[ProductBlockRead]


class QuoteItem(BaseModel):
    product_id: int
    package_count: int = Field(default=1, ge=1, le=100)


class QuoteRequest(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    customer_whatsapp: str = Field(pattern=r"^\d{10,15}$")
    items: list[QuoteItem] = Field(min_length=1, max_length=50)


class QuoteResponse(BaseModel):
    message: str
    whatsapp_url: str | None
    email_url: str | None
    estimated_total: Decimal | None
