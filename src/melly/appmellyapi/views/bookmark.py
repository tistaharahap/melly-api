from typing import Annotated

from fastapi import APIRouter, Depends
from typing_extensions import Doc

from melly.appmellyapi.auth import jwt_auth
from melly.libaccount.domain.account import Account
from melly.libcollection.domain.bookmark import Bookmark
from melly.libcollection.models import BookmarkItemIn, BookmarkItemOut
from melly.libshared.models import TokenPayload

bookmark_router = APIRouter()


@bookmark_router.post(
    "/bookmarks",
    summary="Create bookmark",
    tags=["Bookmark"],
    response_model=BookmarkItemOut,
    status_code=201,
)
async def create_bookmark(
    payload: BookmarkItemIn,
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
    return await Bookmark.create_bookmark(payload=payload, user=user)


@bookmark_router.get(
    "/bookmarks/{slug}",
    summary="Get bookmark by slug",
    tags=["Bookmark"],
    response_model=BookmarkItemOut,
)
async def bookmark_by_slug(
    slug: Annotated[
        str,
        Doc("""
            The slug of the bookmark.
        """),
    ],
):
    return await Bookmark.get_bookmark_by_slug(slug=slug)


@bookmark_router.put(
    "/bookmarks/{slug}",
    summary="Update bookmark by slug",
    tags=["Bookmark"],
    response_model=BookmarkItemOut,
)
async def update_bookmark_by_slug(
    slug: Annotated[
        str,
        Doc("""
            The slug of the bookmark.
        """),
    ],
    payload: Annotated[
        BookmarkItemIn,
        Doc("""
            The bookmark payload.
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
    return await Bookmark.update_bookmark(slug=slug, payload=payload, user=user)
