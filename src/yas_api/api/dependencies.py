from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from yas_api.core.security import decode_access_token
from yas_api.db.session import get_db
from yas_api.models import AdminUser

DbSession = Annotated[Session, Depends(get_db)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/auth/token")


def get_current_admin(
    db: DbSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> AdminUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    subject = decode_access_token(token)
    if subject is None or not subject.isdigit():
        raise credentials_error
    admin = db.get(AdminUser, int(subject))
    if admin is None or not admin.is_active:
        raise credentials_error
    return admin


CurrentAdmin = Annotated[AdminUser, Depends(get_current_admin)]
