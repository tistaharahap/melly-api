from typing import List

from beanie import Document
from pydantic import HttpUrl, Field

from melly.libshared.models import BaseDateTimeMeta, BaseMellyAPIModel


class BookmarkItem(Document, BaseDateTimeMeta):
    url: HttpUrl
    tags: List[str] = Field(default_factory=list)
    content: str | None = None
    slug: str
    owner_id: str

    class Settings:
        name = "bookmark-items"


class BookmarkItemIn(BaseMellyAPIModel):
    url: HttpUrl
    tags: List[str] = Field(default_factory=list)
    content: str | None = None


class BookmarkItemOut(BookmarkItemIn):
    slug: str

    owner_name: str
    owner_picture: HttpUrl | None = None
    owner_id: str
