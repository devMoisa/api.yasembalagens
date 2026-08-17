from pydantic import BaseModel

from yas_api.schemas.common import Timestamped


class MediaRead(Timestamped):
    filename: str
    public_url: str
    mime_type: str
    alt_text: str | None


class MediaUpdate(BaseModel):
    alt_text: str | None = None
