import uuid
from datetime import datetime
from secrets import token_hex
from typing import Literal, List

import pytz
from beanie import Document
from pydantic import EmailStr, HttpUrl, Field, IPvAnyAddress

from melly.libshared.models import BaseDateTimeMeta, BaseMellyAPIModel


class User(Document, BaseDateTimeMeta):
    email: EmailStr
    name: str
    picture: HttpUrl | None = None
    username: str

    auth_provider: Literal["google"]
    auth_provider_user_id: List[str] = Field(default_factory=list)

    identifier: str = Field(default_factory=lambda: str(uuid.uuid4()))

    class Settings:
        name = "users"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    async def reactivate(self) -> None:
        self.deleted_at = None
        await self.save()


class SocialAuthSession(Document, BaseDateTimeMeta):
    nonce: str = Field(default_factory=lambda: token_hex(55))
    extra: dict

    ip: IPvAnyAddress | None = None
    user_agent: str | None = None

    auth_provider: Literal["google"]
    auth_provider_user_id: str | None = None
    auth_provider_access_token: str | None = None

    profile: dict | None = None

    exchange_code: str | None = None

    class Settings:
        name = "social_auth_sessions"

    async def create_exchange_code(self) -> str:
        self.exchange_code = token_hex(55)
        await self.save()
        return self.exchange_code

    @classmethod
    async def create_session(
        cls,
        extra: dict,
        auth_provider: Literal["google"],
        ip: IPvAnyAddress | None = None,
        user_agent: str | None = None,
    ) -> "SocialAuthSession":
        session = cls(
            extra=extra,
            auth_provider=auth_provider,
            ip=ip,
            user_agent=user_agent,
        )
        await session.save()
        return session

    async def remove_session(self) -> None:
        self.deleted_at = datetime.now(tz=pytz.UTC)
        await self.save()


class AccessTokenResponse(BaseMellyAPIModel):
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")


class RefreshToken(BaseMellyAPIModel):
    refresh_token: str = Field(..., alias="refreshToken")


class MyProfile(BaseMellyAPIModel):
    email: EmailStr
    name: str
    picture: HttpUrl | None = None
    username: str | None = None

    created_at: datetime = Field(..., alias="createdAt")
