from datetime import datetime
from typing import List

import pytz
from coolname import generate_slug
from fastapi import HTTPException

from melly.libaccount.models import User
from melly.libcollection.models import Collection as CollectionModel, CollectionIn, CollectionOut, CollectionTitleIn
from melly.libshared.constants import Sort


class Collection:
    @classmethod
    def build_collection_response(cls, collection: dict) -> CollectionOut:
        owner_name = collection.get("owner").get("name")
        owner_picture = collection.get("owner").get("picture")

        return CollectionOut(**collection, owner_name=owner_name, owner_picture=owner_picture)

    @classmethod
    async def get_collection_by_slug(cls, slug: str, user: User | None = None) -> CollectionOut:
        match = {"$match": {"slug": slug, "deleted_at": {"$eq": None}}}
        if user:
            match = {"$match": {"slug": slug, "owner_id": user.username, "deleted_at": {"$eq": None}}}

        pipeline = [
            match,
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
        result = await CollectionModel.aggregate(pipeline).to_list(length=1)
        if len(result) == 0:
            raise HTTPException(status_code=404, detail="Collection not found")

        return cls.build_collection_response(result[0])

    @classmethod
    async def create_collection(cls, payload: CollectionIn, user: User) -> CollectionOut:
        slug = f"{generate_slug(4)}-{int(datetime.now(tz=pytz.UTC).timestamp())}"
        item = CollectionModel(**payload.model_dump(), slug=slug, owner_id=user.username)
        await item.save()
        return await cls.get_collection_by_slug(slug=slug)

    @classmethod
    async def get_my_collections(
        cls, user: User, skip: int = 0, limit: int = 10, sort: Sort = Sort.Descending
    ) -> List[CollectionOut]:
        sort_order = -1 if sort == Sort.Descending else 1
        pipeline = [
            {"$match": {"owner_id": user.username, "deleted_at": {"$eq": None}}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "owner_id",
                    "foreignField": "username",
                    "as": "owner",
                }
            },
            {"$unwind": "$owner"},
            {"$sort": {"created_at": sort_order}},
            {"$skip": skip},
            {"$limit": limit},
        ]
        result = await CollectionModel.aggregate(pipeline).to_list(length=limit)
        return [cls.build_collection_response(collection) for collection in result]

    @classmethod
    async def update_collection(cls, slug: str, payload: CollectionTitleIn, user: User) -> CollectionOut:
        query = {"slug": slug, "owner_id": user.username}
        item = await CollectionModel.find_one(query)
        if not item:
            raise HTTPException(status_code=404, detail="Collection not found")

        item.title = payload.title
        await item.save()

        return await cls.get_collection_by_slug(slug=slug)

    @classmethod
    async def add_bookmark_to_collection(cls, slug: str, bookmark_slug: str, user: User) -> CollectionOut:
        query = {"slug": slug, "owner_id": user.username}
        item = await CollectionModel.find_one(query)
        if not item:
            raise HTTPException(status_code=404, detail="Collection not found")

        if bookmark_slug in item.items:
            raise HTTPException(status_code=400, detail="Bookmark already in collection")

        item.items.append(bookmark_slug)
        await item.save()

        return await cls.get_collection_by_slug(slug=slug)
