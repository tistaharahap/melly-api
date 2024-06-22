from fastapi_jwt_auth3.jwtauth import FastAPIJWTAuth
from jwcrypto import jwk

from melly.libshared.models import TokenPayload
from melly.libshared.settings import api_settings

jwk_key = jwk.JWK.from_pem(api_settings.auth_public_key.encode("utf-8"))
public_key_id = jwk_key.get("kid")
jwt_auth = FastAPIJWTAuth(
    algorithm=api_settings.auth_algorithm,
    base_url=api_settings.base_url,
    audience=api_settings.base_url,
    issuer=api_settings.base_url,
    secret_key=api_settings.auth_private_key,
    public_key=api_settings.auth_public_key,
    public_key_id=public_key_id,
    expiry=api_settings.auth_token_expiry,
    leeway=0,
    project_to=TokenPayload,
)
