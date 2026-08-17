from sqlalchemy.orm import Session

from yas_api.models import StoreSettings


def get_or_create_store_settings(db: Session) -> StoreSettings:
    store_settings = db.get(StoreSettings, 1)
    if store_settings is None:
        store_settings = StoreSettings(id=1)
        db.add(store_settings)
        db.commit()
        db.refresh(store_settings)
    return store_settings
