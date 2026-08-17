from fastapi import APIRouter, Depends

from yas_api.api.dependencies import DbSession, get_current_admin
from yas_api.schemas.catalog import StoreSettingsRead, StoreSettingsUpdate
from yas_api.services.settings import get_or_create_store_settings

router = APIRouter(dependencies=[Depends(get_current_admin)])


@router.get("", response_model=StoreSettingsRead)
def read_settings(db: DbSession):
    return get_or_create_store_settings(db)


@router.patch("", response_model=StoreSettingsRead)
def update_settings(payload: StoreSettingsUpdate, db: DbSession):
    settings = get_or_create_store_settings(db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return settings
