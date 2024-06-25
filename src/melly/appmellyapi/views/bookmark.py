from enum import Enum
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query, Path
from typing_extensions import Doc

from melly.appmellyapi.auth import jwt_auth
from melly.libaccount.domain.account import Account
from melly.libcollection.domain.bookmark import Bookmark
from melly.libcollection.models import BookmarkItemIn, BookmarkItemOut, BookmarkNoteIn
from melly.libshared.models import TokenPayload

bookmark_router = APIRouter()


class Descriptions(str, Enum):
    """
    Parameter descriptions for the bookmark_router endpoints.
    """

    Skip = "The number of bookmarks to skip."
    Limit = "The number of bookmarks to return."
    Slug = "The slug of the bookmark."


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
    "/bookmarks",
    summary="My bookmarks",
    tags=["Bookmark"],
    response_model=List[BookmarkItemOut],
)
async def my_bookmarks(
    skip: Annotated[
        int,
        Doc(Descriptions.Skip.value),
    ] = Query(0, description=Descriptions.Skip.value),
    limit: Annotated[
        int,
        Doc(Descriptions.Limit.value),
    ] = Query(10, description=Descriptions.Limit.value),
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
    return await Bookmark.my_bookmarks(user=user, skip=skip, limit=limit)


@bookmark_router.get(
    "/bookmarks/{slug}",
    summary="Get bookmark by slug",
    tags=["Bookmark"],
    response_model=BookmarkItemOut,
)
async def bookmark_by_slug(
    slug: Annotated[
        str,
        Doc(Descriptions.Slug.value),
    ] = Path(..., description=Descriptions.Slug.value),
):
    return await Bookmark.get_bookmark_by_slug(slug=slug)


@bookmark_router.put(
    "/bookmarks/{slug}",
    summary="Update bookmark by slug",
    tags=["Bookmark"],
    response_model=BookmarkItemOut,
)
async def update_bookmark_by_slug(
    payload: Annotated[
        BookmarkItemIn,
        Doc("""
            The bookmark payload.
        """),
    ],
    slug: Annotated[
        str,
        Doc(Descriptions.Slug.value),
    ] = Path(..., description=Descriptions.Slug.value),
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


@bookmark_router.post(
    "/bookmarks/{slug}/notes",
    summary="Add note to bookmark",
    tags=["Bookmark"],
    response_model=BookmarkItemOut,
    status_code=201,
)
async def add_note(
    payload: Annotated[
        BookmarkNoteIn,
        Doc("""
            The bookmark note payload.
        """),
    ],
    slug: Annotated[
        str,
        Doc(Descriptions.Slug.value),
    ] = Path(..., description=Descriptions.Slug.value),
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
    return await Bookmark.create_note(payload=payload, slug=slug, user=user)
