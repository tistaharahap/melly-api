from datetime import datetime

import pytz
from coolname import generate_slug
from fastapi import HTTPException

from melly.libaccount.models import User
from melly.libcollection.models import BookmarkItem, BookmarkItemOut, BookmarkItemIn


class Bookmark:
    @classmethod
    def build_bookmark_response(cls, bookmark: dict) -> BookmarkItemOut:
        owner_name = bookmark.get("owner").get("name")
        owner_picture = bookmark.get("owner").get("picture")

        return BookmarkItemOut(**bookmark, owner_name=owner_name, owner_picture=owner_picture)

    @classmethod
    async def get_bookmark_by_slug(cls, slug: str) -> BookmarkItemOut:
        pipeline = [
            {"$match": {"slug": slug, "deleted_at": {"$eq": None}}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "owner_id",
                    "foreignField": "username",
                    "as": "owner",
                }
            },
            {"$unwind": "$owner"},
        ]
        result = await BookmarkItem.aggregate(pipeline).to_list(length=1)
        if len(result) == 0:
            raise HTTPException(status_code=404, detail="Bookmark item not found")
        return cls.build_bookmark_response(result[0])

    @classmethod
    async def create_bookmark(cls, payload: BookmarkItemIn, user: User) -> BookmarkItemOut:
        slug = f"{generate_slug(4)}-{int(datetime.now(tz=pytz.UTC).timestamp())}"
        item = BookmarkItem(**payload.model_dump(), slug=slug, owner_id=user.username)
        await item.save()
        return await cls.get_bookmark_by_slug(slug=slug)

    @classmethod
    async def update_bookmark(cls, slug: str, payload: BookmarkItemIn, user: User) -> BookmarkItemOut:
        query = {"slug": slug, "owner_id": user.username}
        item = await BookmarkItem.find_one(query)
        if not item:
            raise HTTPException(status_code=404, detail="Bookmark item not found")

        item.url = payload.url
        item.tags = payload.tags
        item.content = payload.content
        await item.save()

        return await cls.get_bookmark_by_slug(slug=slug)
