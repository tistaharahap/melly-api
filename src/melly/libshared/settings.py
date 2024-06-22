import base64
from functools import lru_cache
from typing import Literal

from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings


class MellyAPISettings(BaseSettings):
    # Base URLs
    base_url: HttpUrl = "http://localhost:8000"
    fe_base_url: HttpUrl = "http://localhost:3000"

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    env: str = "dev"
    cors_origins: str

    # DB
    mongo_url: str = "mongodb://127.0.0.1:27017/?replicaSet=rs0"

    # LLMs
    llm_provider: Literal["openai", "groq", "ollama"] = "openai"
    groq_api_key: str | None = None
    openai_api_key: str | None = None
    ollama_api_key: str | None = None

    # Auth
    auth_algorithm: str = "RS256"
    b64_auth_private_key: str
    b64_auth_public_key: str
    auth_token_expiry: int = 3600

    # Social Providers
    social_auth_expiry_in_seconds: int = 600
    google_client_id: str
    google_client_secret: str

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v):
        return str(v).rstrip("/")

    @field_validator("fe_base_url")
    @classmethod
    def validate_fe_base_url(cls, v):
        return str(v).rstrip("/")

    @property
    def db_name(self) -> str:
        return f"bookmarks-{self.env}"

    @classmethod
    @lru_cache()
    def get_settings(cls):
        return cls()

    @property
    def auth_private_key(self) -> str:
        return base64.b64decode(self.b64_auth_private_key).decode()

    @property
    def auth_public_key(self) -> str:
        return base64.b64decode(self.b64_auth_public_key).decode()


api_settings = MellyAPISettings.get_settings()
