import base64
import uuid
from os import environ
from secrets import token_hex
from typing import Tuple

import pytest
import pytest_asyncio
from faker import Faker
from httpx import AsyncClient, ASGITransport

from melly.appmellyapi.db import api_models
from melly.appmellyapi.web import app, lifespan
from melly.libaccount.models import SocialAuthSession

fake = Faker()


@pytest_asyncio.fixture(autouse=True)
async def api_client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testapi") as ac:
        async with lifespan(app=app):
            for model in api_models:
                await model.delete_all()

            yield ac


@pytest.fixture(scope="session")
def rsa_keypair_from_env() -> Tuple[str, str]:
    private_key = environ.get("B64_AUTH_PRIVATE_KEY")
    public_key = environ.get("B64_AUTH_PUBLIC_KEY")
    return base64.b64decode(private_key).decode("utf-8"), base64.b64decode(public_key).decode("utf-8")


@pytest_asyncio.fixture(scope="function")
async def google_auth():
    async def authorize_google(session: SocialAuthSession, *args, **kwargs) -> Tuple[str, str, str]:
        session.auth_provider_access_token = token_hex(23)
        session.auth_provider_user_id = str(uuid.uuid4())
        session.profile = {
            "name": fake.name(),
            "email": fake.email(),
            "picture": fake.image_url(),
        }
        await session.save()

        return session.profile.get("email"), session.profile.get("name"), session.profile.get("picture")

    from melly.libaccount.domain.account import Account

    Account.authorize_google = authorize_google
