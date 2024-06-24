from typing import Annotated, List

from fastapi import APIRouter, Depends
from typing_extensions import Doc

from melly.appmellyapi.auth import jwt_auth
from melly.libaccount.domain.account import Account
from melly.libcollection.domain.bookmark import Bookmark
from melly.libcollection.domain.collection import Collection
from melly.libcollection.models import CollectionOut, CollectionIn, CollectionTitleIn, SlugIn
from melly.libshared.models import TokenPayload

collection_router = APIRouter()


@collection_router.post(
    "/me/collections",
    summary="Create collection",
    tags=["Collection"],
    response_model=CollectionOut,
    status_code=201,
)
async def create_collection(
    payload: CollectionIn,
    claims: Annotated[
        TokenPayload,
        Doc("""
            The projection model for the JWT token.
        """),
    ] = Depends(jwt_auth),
):
    user = await Account.get_user_by_email(
        email=claims.email, raise_for_error=True, status_code=401, error_message="Invalid token"
    )
    return await Collection.create_collection(payload=payload, user=user)


@collection_router.get(
    "/me/collections",
    summary="My collections",
    tags=["Collection"],
    response_model=List[CollectionOut],
)
async def my_collections(
    skip: Annotated[
        int,
        Doc("""
            The number of collections to skip.
        """),
    ] = 0,
    limit: Annotated[
        int,
        Doc("""
            The number of collections to limit.
        """),
    ] = 10,
    claims: Annotated[
        TokenPayload,
        Doc("""
            The projection model for the JWT token.
        """),
    ] = Depends(jwt_auth),
):
    user = await Account.get_user_by_email(
        email=claims.email, raise_for_error=True, status_code=401, error_message="Invalid token"
    )
    return await Collection.get_my_collections(user=user, skip=skip, limit=limit)


@collection_router.get(
    "/me/collections/{slug}",
    summary="Get collection by slug",
    tags=["Collection"],
    response_model=CollectionOut,
)
async def get_collection_by_slug(
    slug: Annotated[
        str,
        Doc("""
            The slug of the collection.
        """),
    ],
    claims: Annotated[
        TokenPayload,
        Doc("""
            The projection model for the JWT token.
        """),
    ] = Depends(jwt_auth),
):
    user = await Account.get_user_by_email(
        email=claims.email, raise_for_error=True, status_code=401, error_message="Invalid token"
    )
    return await Collection.get_collection_by_slug(slug=slug, user=user)


@collection_router.put(
    "/me/collections/{slug}/title",
    summary="Update collection title",
    tags=["Collection"],
    response_model=CollectionOut,
)
async def update_collection_by_slug(
    slug: Annotated[
        str,
        Doc("""
            The slug of the collection.
        """),
    ],
    payload: CollectionTitleIn,
    claims: Annotated[
        TokenPayload,
        Doc("""
            The projection model for the JWT token.
        """),
    ] = Depends(jwt_auth),
):
    user = await Account.get_user_by_email(
        email=claims.email, raise_for_error=True, status_code=401, error_message="Invalid token"
    )
    return await Collection.update_collection(slug=slug, payload=payload, user=user)


@collection_router.post(
    "/me/collections/{slug}/items",
    summary="Add bookmark to collection",
    tags=["Collection"],
    response_model=CollectionOut,
    status_code=201,
)
async def add_bookmark_to_collection(
    slug: Annotated[
        str,
        Doc("""
            The slug of the collection.
        """),
    ],
    payload: SlugIn,
    claims: Annotated[
        TokenPayload,
        Doc("""
            The projection model for the JWT token.
        """),
    ] = Depends(jwt_auth),
):
    await Bookmark.get_bookmark_by_slug(slug=payload.slug)

    user = await Account.get_user_by_email(
        email=claims.email, raise_for_error=True, status_code=401, error_message="Invalid token"
    )
    return await Collection.add_bookmark_to_collection(slug=slug, bookmark_slug=payload.slug, user=user)
