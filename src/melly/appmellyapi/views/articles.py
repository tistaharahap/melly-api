from typing import Annotated, List

from fastapi import APIRouter, Depends
from typing_extensions import Doc

from melly.appmellyapi.auth import jwt_auth
from melly.libaccount.domain.account import Account
from melly.libarticle.domain.article import Article
from melly.libarticle.models import ArticleOut, ArticleIn
from melly.libshared.models import TokenPayload

article_router = APIRouter()


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
        Doc("""
            The number of articles to skip.
        """),
    ] = 0,
    limit: Annotated[
        int,
        Doc("""
            The number of articles to skip.
        """),
    ] = 10,
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
        Doc("""
            The slug of the article.
        """),
    ],
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
    slug: Annotated[
        str,
        Doc("""
            The slug of the article.
        """),
    ],
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
    return await Article.update_article(slug=slug, payload=payload, user=user)
