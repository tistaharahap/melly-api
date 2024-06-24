from secrets import token_hex
from urllib.parse import urlparse, parse_qs

import pytest
import ujson
from httpx import AsyncClient

from melly.libaccount.models import AccessTokenResponse, MyProfile


@pytest.mark.asyncio
async def test_auth(api_client: AsyncClient, google_auth):
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
