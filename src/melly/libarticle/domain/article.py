from datetime import datetime
from typing import List

import pytz
from fastapi import HTTPException
from slugify import slugify

from melly.libaccount.models import User
from melly.libarticle.models import Article as ArticleModel, ArticleOut, ArticleIn
from melly.libshared.constants import Sort
from melly.libshared.settings import api_settings


class Article:
    @classmethod
    def build_article_response(cls, article: dict) -> ArticleOut:
        canonical_url = f"{api_settings.fe_base_url}/articles/{article.get('slug')}"

        return ArticleOut(
            title=article.get("title"),
            description=article.get("description"),
            image=article.get("image"),
            slug=article.get("slug"),
            content_in_markdown=article.get("content_in_markdown"),
            author_name=article.get("author").get("name"),
            author_picture=article.get("author").get("picture"),
            author_id=article.get("author").get("username"),
            created_at=article.get("created_at"),
            canonical_url=canonical_url,
        )

    @classmethod
    async def get_my_articles(
        cls, user: User, skip: int = 0, limit: int = 10, sort: Sort = Sort.Descending
    ) -> List[ArticleOut]:
        sort_direction = -1 if sort.value == Sort.Descending.value else 1
        pipeline = [
            {"$match": {"author_id": user.identifier, "deleted_at": {"$eq": None}}},
            {"$skip": skip},
            {"$limit": limit},
            {"$sort": {"created_at": sort_direction}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "author_id",
                    "foreignField": "identifier",
                    "as": "author",
                }
            },
            {"$unwind": "$author"},
        ]
        articles = await ArticleModel.aggregate(pipeline).to_list()
        return [cls.build_article_response(x) for x in articles]

    @classmethod
    async def get_article_by_slug(cls, slug: str) -> ArticleOut:
        pipeline = [
            {"$match": {"slug": slug, "deleted_at": {"$eq": None}}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "author_id",
                    "foreignField": "identifier",
                    "as": "author",
                }
            },
            {"$unwind": "$author"},
        ]
        articles = await ArticleModel.aggregate(pipeline).to_list(length=1)
        if len(articles) == 0:
            raise HTTPException(status_code=404, detail="Article not found")

        article = articles[0]
        return cls.build_article_response(article)

    @classmethod
    async def create_article(cls, payload: ArticleIn, user: User) -> ArticleOut:
        now = datetime.now(tz=pytz.UTC)
        slug = f"{slugify(payload.title)}-{int(now.timestamp())}"
        article = ArticleModel(**payload.model_dump(), slug=slug, author_id=user.identifier)
        await article.save()
        return await cls.get_article_by_slug(slug=slug)

    @classmethod
    async def update_article(cls, payload: ArticleIn, user: User, slug: str) -> ArticleOut:
        article = await ArticleModel.find_one({"slug": slug, "author_id": user.identifier})
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")

        article.title = payload.title
        article.description = payload.description
        article.image = payload.image
        article.content_in_markdown = payload.content_in_markdown
        await article.save()

        return await cls.get_article_by_slug(slug=slug)
