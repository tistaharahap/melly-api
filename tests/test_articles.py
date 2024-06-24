from secrets import token_hex
from urllib.parse import urlparse, parse_qs

import pytest
import ujson
from faker import Faker
from httpx import AsyncClient

from melly.libaccount.models import AccessTokenResponse
from melly.libarticle.models import ArticleOut
from melly.libshared.models import MyProfile

fake = Faker()


@pytest.mark.asyncio
async def test_articles(api_client: AsyncClient, google_auth):
    extra = {"key": token_hex(55)}
    params = {"extra": ujson.dumps(extra)}
    response = await api_client.get("/v1/me/auth/google", params=params)

    assert response.status_code == 200

    resp_body = response.json()
    auth_url: str = resp_body.get("url")

    assert auth_url.startswith("https://accounts.google.com/o/oauth2/auth?response_type=code")

    parsed_url = urlparse(auth_url)
    query_strings = parse_qs(parsed_url.query)

    params = {"state": query_strings.get("state"), "code": token_hex(23)}
    response = await api_client.get("/v1/me/auth/google/callback", params=params)

    assert response.status_code == 302
    assert response.headers.get("location").startswith("http://localhost:3000")

    fe_url = urlparse(response.headers.get("location"))
    fe_query_strings = parse_qs(fe_url.query)

    code = fe_query_strings.get("code")

    response = await api_client.get("/v1/me/access/token", params={"code": code})

    assert response.status_code == 200

    access_token_response = AccessTokenResponse(**response.json())

    assert access_token_response.access_token
    assert access_token_response.refresh_token

    headers = {"authorization": f"Bearer {access_token_response.access_token}"}
    response = await api_client.get("/v1/me", headers=headers)

    assert response.status_code == 200

    my_profile = MyProfile(**response.json())

    assert my_profile.email
    assert my_profile.name
    assert my_profile.picture

    # Create article
    payload = {
        "title": fake.street_name(),
        "description": fake.sentence(),
        "image": fake.image_url(),
        "content_in_markdown": "# Hello\nWorld.",
    }
    response = await api_client.post("/v1/articles", json=payload, headers=headers)

    assert response.status_code == 201

    article = ArticleOut(**response.json())

    assert article.title == payload.get("title")
    assert article.description == payload.get("description")
    assert str(article.image) == str(payload.get("image"))
    assert article.content_in_markdown == payload.get("content_in_markdown")
    assert article.author_name == my_profile.name
    assert str(article.author_picture) == str(my_profile.picture)
    assert article.slug
    assert article.created_at

    # My articles
    response = await api_client.get("/v1/articles", headers=headers)

    assert response.status_code == 200

    articles = [ArticleOut(**x) for x in response.json()]

    assert len(articles) == 1
    assert articles[0].slug == article.slug

    # Article profile
    response = await api_client.get(f"/v1/articles/{article.slug}")

    assert response.status_code == 200

    article_profile = ArticleOut(**response.json())

    assert article_profile.slug == article.slug

    # Update article
    update_payload = payload.copy()
    update_payload.update({"title": fake.street_name()})

    response = await api_client.put(f"/v1/articles/{article.slug}", json=update_payload, headers=headers)

    assert response.status_code == 200

    updated_article = ArticleOut(**response.json())

    assert updated_article.title == update_payload.get("title")
    assert updated_article.slug == article.slug
