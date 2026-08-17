import mimetypes
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from yas_api.api.dependencies import DbSession, get_current_admin
from yas_api.core.config import settings
from yas_api.core.storage import get_storage
from yas_api.models import Media
from yas_api.schemas.media import MediaRead, MediaUpdate

router = APIRouter(dependencies=[Depends(get_current_admin)])
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.get("", response_model=list[MediaRead])
def list_media(db: DbSession):
    return db.scalars(select(Media).order_by(Media.created_at.desc())).all()


@router.post("", response_model=MediaRead, status_code=status.HTTP_201_CREATED)
async def upload_media(
    db: DbSession,
    file: Annotated[UploadFile, File()],
    alt_text: Annotated[str | None, Form()] = None,
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Envie uma imagem JPEG, PNG, WebP ou GIF")

    limit = settings.max_upload_size_mb * 1024 * 1024
    content = await file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"A imagem deve ter no maximo {settings.max_upload_size_mb} MB",
        )

    suffix = mimetypes.guess_extension(file.content_type) or Path(file.filename or "").suffix
    stored_filename = f"{uuid4().hex}{suffix}"
    prefix = settings.spaces_key_prefix.strip("/")
    key = f"{prefix}/{stored_filename}" if prefix else stored_filename

    storage = get_storage()
    stored = storage.upload(key=key, content=content, content_type=file.content_type)

    media = Media(
        filename=file.filename or stored_filename,
        storage_path=stored.key,
        public_url=stored.public_url,
        mime_type=file.content_type,
        alt_text=alt_text,
    )
    db.add(media)
    try:
        db.commit()
    except Exception:
        storage.delete(key=stored.key)
        raise
    db.refresh(media)
    return media


@router.patch("/{media_id}", response_model=MediaRead)
def update_media(media_id: int, payload: MediaUpdate, db: DbSession):
    media = db.get(Media, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Imagem nao encontrada")
    media.alt_text = payload.alt_text
    db.commit()
    db.refresh(media)
    return media


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(media_id: int, db: DbSession) -> Response:
    media = db.get(Media, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Imagem nao encontrada")
    stored_key = media.storage_path
    db.delete(media)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A imagem ainda esta em uso") from exc
    get_storage().delete(key=stored_key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
