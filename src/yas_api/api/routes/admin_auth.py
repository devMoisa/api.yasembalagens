from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from yas_api.api.dependencies import CurrentAdmin, DbSession
from yas_api.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    verify_password,
)
from yas_api.models import AdminUser
from yas_api.schemas.auth import AdminUserRead, Token

router = APIRouter()


@router.post("/token", response_model=Token)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> Token:
    admin = db.scalar(select(AdminUser).where(AdminUser.email == form.username.lower()))
    if admin is None:
        verify_password(form.password, DUMMY_PASSWORD_HASH)
    if (
        admin is None
        or not admin.is_active
        or not verify_password(form.password, admin.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(str(admin.id)))


@router.get("/me", response_model=AdminUserRead)
def me(admin: CurrentAdmin) -> AdminUser:
    return admin
