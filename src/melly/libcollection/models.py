from datetime import datetime
from typing import List

import pytz
from beanie import Document, before_event, Replace, Update, SaveChanges
from pydantic import HttpUrl, Field

from melly.libshared.models import BaseDateTimeMeta, BaseMellyAPIModel


class BookmarkItem(Document, BaseDateTimeMeta):
    url: HttpUrl
    tags: List[str] = Field(default_factory=list)
    content: str | None = None
    slug: str
    owner_id: str

    @before_event(Replace, Update, SaveChanges)
    async def bump_updated_at(self):
        self.updated_at = datetime.now(tz=pytz.UTC)

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

    created_at: datetime
    updated_at: datetime | None = None
