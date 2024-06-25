from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from typing_extensions import Doc

from fastapi import Request

from melly.appmellyapi.auth import jwt_auth
from melly.libaccount.domain.account import Account
from melly.libaccount.models import AccessTokenResponse, RefreshToken, MyProfile, UsernameIn
from melly.libshared.models import UrlResponse, TokenPayload

me_router = APIRouter()


class Descriptions(str, Enum):
    """
    Parameter descriptions for the me_router endpoints.
    """

    LoginUrlExtra = "Extra state params encoded as a JSON string. Will be returned when redirected back to the FE."
    OauthCallbackState = "The state from the OAuth session returned by the OAuth provider."
    OauthCallbackCode = "The authorization code from the OAuth provider."
    AccessTokenCode = "The authorization code from the API given to the FE to exchange for an access token."


@me_router.get(
    "/me/auth/google",
    summary="Get Google Login URL",
    tags=["me", "auth"],
    response_model=UrlResponse,
)
async def get_google_login_url(
    request: Request,
    extra: Annotated[
        str | None,
        Doc(Descriptions.LoginUrlExtra.value),
    ] = Query(
        None,
        description=Descriptions.LoginUrlExtra.value,
    ),
):
    return await Account.create_login_url(request=request, extra=extra, provider="google")


@me_router.get(
    "/me/auth/google/callback",
    summary="Google Auth Callback",
    tags=["me", "auth"],
    response_class=RedirectResponse,
)
async def google_auth_callback(
    state: Annotated[
        str,
        Doc(Descriptions.OauthCallbackState.value),
    ] = Query(..., description=Descriptions.OauthCallbackState.value),
    code: Annotated[
        str,
        Doc(Descriptions.OauthCallbackState.value),
    ] = Query(..., description=Descriptions.OauthCallbackCode.value),
):
    session = await Account.get_auth_session(nonce=state)
    email, name, picture = await Account.authorize_google(code=code, session=session)
    await Account.maybe_create_user(email=email, name=name, picture=picture, session=session)

    fe_redir_url = await Account.get_fe_redirect_url(session=session)

    return RedirectResponse(url=fe_redir_url, status_code=302)


@me_router.get(
    "/me/access/token",
    summary="Exchange authorization code for access token",
    tags=["me", "auth"],
    response_model=AccessTokenResponse,
)
async def exchange_code(
    code: Annotated[
        str,
        Doc(Descriptions.AccessTokenCode.value),
    ] = Query(..., description=Descriptions.AccessTokenCode.value),
):
    return await Account.exchange_code(code=code)


@me_router.post(
    "/me/access/token/refresh",
    summary="Exchange refresh token for access token",
    tags=["me", "auth"],
    response_model=AccessTokenResponse,
)
async def exchange_refresh_token(payload: RefreshToken):
    return await Account.exchange_refresh_token(payload=payload)


@me_router.get(
    "/me",
    summary="Get my profile",
    tags=["me"],
    response_model=MyProfile,
)
async def my_profile(
    claims: Annotated[
        TokenPayload,
        Doc("""
            The projection model for the JWT token.
        """),
    ] = Depends(jwt_auth),
):
    user = await Account.get_user_by_email(email=claims.email)
    return MyProfile(**user.model_dump())


@me_router.put(
    "/me/username",
    summary="Update my username",
    tags=["me"],
    response_model=MyProfile,
)
async def update_username(
    payload: UsernameIn,
    claims: Annotated[
        TokenPayload,
        Doc("""
            The projection model for the JWT token.
        """),
    ] = Depends(jwt_auth),
):
    user = await Account.get_user_by_email(email=claims.email)
    return await Account.update_username(payload=payload, user=user)
