from secrets import token_hex
from urllib.parse import urlparse, parse_qs

import pytest
import ujson
from faker import Faker
from httpx import AsyncClient

from melly.libaccount.models import AccessTokenResponse, MyProfile
from melly.libcollection.models import BookmarkItemOut, CollectionOut

fake = Faker()


@pytest.mark.asyncio
async def test_collection(api_client: AsyncClient, google_auth):
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
    assert my_profile.username

    # Update username
    payload = {"username": token_hex(23)}

    response = await api_client.put("/v1/me/username", headers=headers, json=payload)

    assert response.status_code == 200

    updated_profile = MyProfile(**response.json())

    assert updated_profile.username == payload.get("username")

    # Create bookmark
    payload = {
        "url": fake.url(),
        "tags": [fake.word() for _ in range(5)],
        "content": "\n\n".join(fake.sentences(nb=10)),
    }

    response = await api_client.post("/v1/bookmarks", json=payload, headers=headers)

    assert response.status_code == 201

    bookmark = BookmarkItemOut(**response.json())

    assert str(bookmark.url) == str(payload.get("url"))
    assert bookmark.tags == payload.get("tags")
    assert bookmark.content == payload.get("content")
    assert bookmark.owner_name == my_profile.name
    assert bookmark.owner_picture == my_profile.picture
    assert bookmark.slug

    # Create collection
    payload = {"title": fake.street_name()}

    response = await api_client.post("/v1/me/collections", json=payload, headers=headers)

    assert response.status_code == 201

    collection = CollectionOut(**response.json())

    assert collection.title == payload.get("title")
    assert collection.owner_name == my_profile.name
    assert collection.owner_picture == my_profile.picture
    assert collection.slug
    assert len(collection.items) == 0

    # My collections
    response = await api_client.get("/v1/me/collections", headers=headers)

    assert response.status_code == 200

    collections = [CollectionOut(**x) for x in response.json()]

    assert len(collections) == 1
    assert collections[0].slug == collection.slug

    # Collection profile
    response = await api_client.get(f"/v1/me/collections/{collection.slug}", headers=headers)

    assert response.status_code == 200

    collection_profile = CollectionOut(**response.json())

    assert collection_profile.slug == collection.slug

    # Add bookmark to collection
    payload = {"slug": bookmark.slug}

    response = await api_client.post(f"/v1/me/collections/{collection.slug}/items", json=payload, headers=headers)

    assert response.status_code == 201

    updated_collection = CollectionOut(**response.json())

    assert updated_collection.slug == collection.slug
    assert len(updated_collection.items) == 1
    assert updated_collection.items[0] == bookmark.slug
