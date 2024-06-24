from datetime import datetime
from typing import List

import pytz
from beanie import Document, before_event, Replace, Update, SaveChanges
from coolname import generate_slug
from pydantic import HttpUrl, Field

from melly.libshared.models import BaseDateTimeMeta, BaseMellyAPIModel


class BookmarkNote(BaseMellyAPIModel):
    content: str
    slug: str = Field(default_factory=lambda: f"{generate_slug(3)}-{int(datetime.now(tz=pytz.UTC).timestamp())}")
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(tz=pytz.UTC))


class BookmarkNoteOut(BaseMellyAPIModel):
    content: str
    slug: str
    created_at: datetime = Field(alias="createdAt")


class BookmarkItem(Document, BaseDateTimeMeta):
    url: HttpUrl
    tags: List[str] = Field(default_factory=list)
    content: str | None = None
    slug: str
    owner_id: str

    notes: List[BookmarkNote] = Field(default_factory=list)

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
    notes: List[BookmarkNoteOut] | None = Field(default_factory=list)

    slug: str

    owner_name: str
    owner_picture: HttpUrl | None = None
    owner_id: str

    created_at: datetime
    updated_at: datetime | None = None


class BookmarkNoteIn(BaseMellyAPIModel):
    content: str


class Collection(Document, BaseDateTimeMeta):
    title: str
    slug: str
    owner_id: str

    items: List[str] = Field(default_factory=list)

    published_at: datetime | None = None

    async def publish(self) -> "Collection":
        self.published_at = datetime.now(tz=pytz.UTC)
        await self.save()
        return self

    async def unpublish(self) -> "Collection":
        self.published_at = None
        await self.save()
        return self

    @property
    def is_published(self) -> bool:
        return self.published_at is not None

    @before_event(Replace, Update, SaveChanges)
    async def bump_updated_at(self):
        self.updated_at = datetime.now(tz=pytz.UTC)

    class Settings:
        name = "collections"


class SlugIn(BaseMellyAPIModel):
    slug: str


class CollectionTitleIn(BaseMellyAPIModel):
    title: str
    items: List[str] = Field(default_factory=list)


class CollectionIn(CollectionTitleIn):
    items: List[str] = Field(default_factory=list)


class CollectionOut(CollectionIn):
    slug: str
    owner_name: str
    owner_picture: HttpUrl | None = None
    owner_id: str

    published_at: datetime | None = None

    created_at: datetime
    updated_at: datetime | None = None


class CollectionComment(Document, BaseDateTimeMeta):
    content: str
    author_id: str

    collection_slug: str

    slug: str
    parent_comment_slug: str | None = None

    class Settings:
        name = "collection-comments"
