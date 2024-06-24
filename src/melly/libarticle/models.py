from datetime import datetime

import pytz
from beanie import Document, before_event, Replace, Update, SaveChanges
from pydantic import HttpUrl, Field

from melly.libshared.models import BaseDateTimeMeta, BaseMellyAPIModel


class Article(Document, BaseDateTimeMeta):
    title: str
    description: str
    image: HttpUrl | None = None

    slug: str
    content_in_markdown: str

    author_id: str

    @before_event(Replace, Update, SaveChanges)
    async def bump_updated_at(self):
        self.updated_at = datetime.now(tz=pytz.UTC)

    class Settings:
        name = "articles"


class ArticleIn(BaseMellyAPIModel):
    title: str
    description: str
    image: HttpUrl | None = None

    content_in_markdown: str = Field(..., alias="contentInMarkdown")


class ArticleOut(ArticleIn):
    slug: str

    author_name: str = Field(..., alias="authorName")
    author_picture: HttpUrl | None = Field(..., alias="authorPicture")
    author_id: str

    canonical_url: HttpUrl = Field(..., alias="canonicalUrl")

    created_at: datetime = Field(..., alias="createdAt")
