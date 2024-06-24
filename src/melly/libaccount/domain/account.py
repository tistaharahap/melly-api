from secrets import token_hex
from typing import Literal, Tuple

import httpx
import ujson
from bson import ObjectId
from fastapi import Request, HTTPException
from fastapi_jwt_auth3.errors import JWTDecodeError
from fastapi_jwt_auth3.jwtauth import generate_jwt_token, verify_token
from fastapi_jwt_auth3.models import JWTPresetClaims
from pydantic import IPvAnyAddress, ValidationError
from slugify import slugify

from melly.appmellyapi.auth import jwt_auth
from melly.libaccount.models import SocialAuthSession, User, AccessTokenResponse, RefreshToken, UsernameIn, MyProfile
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
    async def create_login_url(cls, request: Request, extra: str, provider: Literal["google"]) -> UrlResponse:
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
            username=slugify(f"{name}-{session.auth_provider_user_id}-{token_hex(5)}"),
        )
        await user.save()
        return user

    @classmethod
    async def get_user_by_email(
        cls, email: str, raise_for_error: bool = False, status_code: int = 404, error_message: str = "User not found"
    ) -> User | None:
        query = {"email": email}
        user = await User.find_one(query)
        if raise_for_error and not user:
            raise HTTPException(status_code=status_code, detail=error_message)
        return user

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

    @classmethod
    def generate_access_token(cls, user: User) -> str:
        preset_claims = JWTPresetClaims.factory(
            issuer=jwt_auth.issuer,
            expiry=api_settings.auth_token_expiry,
            audience=jwt_auth.audience,
            subject=user.identifier,
        )
        claims = {"email": user.email, "name": user.name, "picture": str(user.picture)}

        return generate_jwt_token(
            header=jwt_auth.header, preset_claims=preset_claims, secret_key=api_settings.auth_private_key, claims=claims
        )

    @classmethod
    def generate_access_and_refresh_token(cls, user: User) -> Tuple[str, str]:
        access_token = cls.generate_access_token(user=user)
        refresh_token = jwt_auth.generate_refresh_token(access_token=access_token)

        return access_token, refresh_token

    @classmethod
    async def exchange_code(cls, code: str) -> AccessTokenResponse:
        query = {"exchange_code": code, "deleted_at": None}
        session = await SocialAuthSession.find_one(query)
        if not session:
            raise HTTPException(status_code=409, detail="Invalid session")

        query = {"auth_provider_user_id": session.auth_provider_user_id, "deleted_at": None}
        user = await User.find_one(query)

        access_token, refresh_token = cls.generate_access_and_refresh_token(user=user)

        return AccessTokenResponse(access_token=access_token, refresh_token=refresh_token)

    @classmethod
    async def exchange_refresh_token(cls, payload: RefreshToken) -> AccessTokenResponse:
        try:
            verified = verify_token(
                token=payload.refresh_token,
                key=api_settings.auth_public_key,
                algorithm=api_settings.auth_algorithm,
                audience=jwt_auth.audience,
                issuer=jwt_auth.issuer,
                leeway=jwt_auth.leeway,
            )
        except JWTDecodeError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        try:
            user_id = ObjectId(verified.get("sub"))
        except TypeError:
            raise HTTPException(status_code=401, detail="Invalid user")

        query = {"_id": user_id, "deleted_at": None}
        user = await User.find_one(query)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")

        access_token = cls.generate_access_token(user=user)

        return AccessTokenResponse(access_token=access_token, refresh_token=payload.refresh_token)

    @classmethod
    async def update_username(cls, payload: UsernameIn, user: User) -> MyProfile:
        query = {"username": payload.username}
        existing_user = await User.find_one(query)
        if existing_user:
            raise HTTPException(status_code=409, detail="Username already exists")

        user.username = payload.username
        await user.save()
        return MyProfile(**user.model_dump())
