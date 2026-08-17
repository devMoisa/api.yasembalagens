from fastapi import APIRouter

from yas_api.api.routes import admin_auth, admin_catalog, admin_media, admin_settings, public

api_router = APIRouter()
api_router.include_router(public.router)
api_router.include_router(admin_auth.router, prefix="/admin/auth", tags=["Admin: autenticacao"])
api_router.include_router(admin_media.router, prefix="/admin/media", tags=["Admin: midia"])
api_router.include_router(admin_catalog.router, prefix="/admin", tags=["Admin: catalogo"])
api_router.include_router(admin_settings.router, prefix="/admin/settings", tags=["Admin: ajustes"])
