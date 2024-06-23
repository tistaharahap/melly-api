from datetime import datetime

import pytz
from pydantic import BaseModel, ConfigDict, Field, EmailStr, HttpUrl


class BaseMellyAPIModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        use_enum_values=True,
        protected_namespaces=(),
    )


class BaseDateTimeMeta(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=pytz.UTC))
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class TokenPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True, populate_by_name=True)

    name: str
    email: EmailStr
    picture: HttpUrl | None = None

    sub: str
    aud: str | None = None
    exp: int
    iss: str
    jti: str
    iat: int
    nbf: int | None = None


class UrlResponse(BaseMellyAPIModel):
    url: HttpUrl


class MyProfile(BaseMellyAPIModel):
    email: EmailStr
    name: str
    picture: HttpUrl | None = None

    created_at: datetime
