from enum import Enum
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query, Path
from typing_extensions import Doc

from melly.appmellyapi.auth import jwt_auth
from melly.libaccount.domain.account import Account
from melly.libarticle.domain.article import Article
from melly.libarticle.models import ArticleOut, ArticleIn
from melly.libshared.models import TokenPayload

article_router = APIRouter()


class Descriptions(str, Enum):
    """
    Parameter descriptions for the article_router endpoints.
    """

    Skip = "The number of articles to skip."
    Limit = "The number of articles to return."
    Slug = "The slug of the article."


@article_router.get(
    "/articles",
    summary="Get my articles",
    tags=["Article"],
    response_model=List[ArticleOut],
)
async def my_articles(
    claims: Annotated[
        TokenPayload,
        Doc("""
            The projection model for the JWT token.
        """),
    ] = Depends(jwt_auth),
    skip: Annotated[
        int,
        Doc(Descriptions.Skip.value),
    ] = Query(0, description=Descriptions.Skip.value),
    limit: Annotated[
        int,
        Doc(Descriptions.Limit.value),
    ] = Query(10, description=Descriptions.Limit.value),
):
    user = await Account.get_user_by_email(
        email=claims.email, raise_for_error=True, status_code=401, error_message="Invalid token"
    )
    return await Article.get_my_articles(user=user, skip=skip, limit=limit)


@article_router.get(
    "/articles/{slug}",
    summary="Get article by slug",
    tags=["Article"],
    response_model=ArticleOut,
)
async def article_by_slug(
    slug: Annotated[
        str,
        Doc(Descriptions.Slug.value),
    ] = Path(..., description=Descriptions.Slug.value),
):
    return await Article.get_article_by_slug(slug=slug)


@article_router.post(
    "/articles",
    summary="Create article",
    tags=["Article"],
    response_model=ArticleOut,
    status_code=201,
)
async def create_article(
    payload: Annotated[
        ArticleIn,
        Doc("""
            The article payload.
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
    return await Article.create_article(payload=payload, user=user)


@article_router.put(
    "/articles/{slug}",
    summary="Update article by slug",
    tags=["Article"],
    response_model=ArticleOut,
)
async def update_article_by_slug(
    payload: Annotated[
        ArticleIn,
        Doc("""
            The article payload.
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
    return await Article.update_article(slug=slug, payload=payload, user=user)
