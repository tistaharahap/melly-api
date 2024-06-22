from typing import Literal, Tuple

import httpx
import ujson
from fastapi import Request, HTTPException
from pydantic import IPvAnyAddress, ValidationError

from melly.libaccount.models import SocialAuthSession, User
from melly.libshared.models import UrlResponse
from melly.libshared.settings import api_settings


class Account:
    @classmethod
    def get_login_url(cls, provider: Literal["google"], nonce: str) -> str:
        if provider == "google":
            client_id = api_settings.google_client_id
            redirect_uri = f"{api_settings.base_url}/v1/me/auth/google/callback"
            return f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=openid%20profile%20email&access_type=offline&state={nonce}"

        raise ValueError("Invalid provider")

    @classmethod
    async def create_social_auth_session(cls, request: Request, extra: str, provider: Literal["google"]) -> UrlResponse:
        try:
            extra = ujson.loads(extra)
        except ujson.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid extra")

        try:
            ip = IPvAnyAddress(request.client.host)
        except ValidationError:
            ip = None

        session = await SocialAuthSession.create_session(
            extra=extra,
            auth_provider=provider,
            ip=ip,
            user_agent=request.headers.get("user-agent"),
        )
        url = cls.get_login_url(provider=provider, nonce=session.nonce)

        return UrlResponse(url=url)

    @classmethod
    async def get_auth_session(cls, nonce: str) -> SocialAuthSession:
        query = {"nonce": nonce, "deleted_at": None}
        session = await SocialAuthSession.find_one(query)
        if not session:
            raise HTTPException(status_code=409, detail="Invalid session")

        # now = datetime.now(tz=pytz.UTC)
        # delta = now - session.created_at.astimezone(tz=pytz.UTC)
        # if delta.seconds > api_settings.social_auth_expiry_in_seconds:
        #     await session.remove_session()
        #     raise HTTPException(status_code=409, detail="Invalid session")

        return session

    @classmethod
    async def authorize_google(cls, session: SocialAuthSession, code: str) -> Tuple[str, str, str]:
        token_url = "https://accounts.google.com/o/oauth2/token"
        user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"

        data = {
            "code": code,
            "client_id": api_settings.google_client_id,
            "client_secret": api_settings.google_client_secret,
            "redirect_uri": f"{api_settings.base_url}/v1/me/auth/google/callback",
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            if response.status_code > 204:
                raise HTTPException(status_code=response.status_code, detail=response.text)

            resp_body = response.json()
            access_token = resp_body.get("access_token")

            headers = {"authorization": f"Bearer {access_token}"}
            response = await client.get(user_info_url, headers=headers)
            if response.status_code > 204:
                raise HTTPException(status_code=response.status_code, detail=response.text)

            resp_body = response.json()

            email = resp_body.get("email")
            name = resp_body.get("name")
            picture = resp_body.get("picture")

            session.auth_provider_access_token = access_token
            session.auth_provider_user_id = resp_body.get("id")
            session.profile = resp_body
            await session.save()

            return email, name, picture

    @classmethod
    async def create_user(cls, email: str, name: str, picture: str, session: SocialAuthSession) -> User:
        user = User(
            email=email,
            name=name,
            picture=picture,
            auth_provider=session.auth_provider,
            auth_provider_user_id=[session.auth_provider_user_id],
        )
        await user.save()
        return user

    @classmethod
    async def get_user_by_email(cls, email: str) -> User | None:
        query = {"email": email}
        return await User.find_one(query)

    @classmethod
    async def maybe_create_user(cls, email: str, name: str, picture: str, session: SocialAuthSession) -> User:
        query = {"email": email}
        user = await User.find_one(query)
        if user and user.is_deleted:
            # Deleted user tried to come back, let's welcome them back
            await user.reactivate()

        if not user:
            user = await cls.create_user(email=email, name=name, picture=picture, session=session)

        return user

    @classmethod
    async def get_fe_redirect_url(cls, session: SocialAuthSession) -> str:
        exchange_code = await session.create_exchange_code()
        extra = ujson.dumps(session.extra)
        redirect_url = f"{api_settings.fe_base_url}/me/auth/google/callback?code={exchange_code}&extra={extra}"
        return redirect_url
