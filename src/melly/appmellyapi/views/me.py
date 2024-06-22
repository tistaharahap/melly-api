from typing import Annotated

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from typing_extensions import Doc

from fastapi import Request

from melly.libaccount.domain.account import Account
from melly.libshared.models import UrlResponse

me_router = APIRouter()


@me_router.get(
    "/me/auth/google",
    summary="Get Google Login URL",
    response_model=UrlResponse,
)
async def get_google_login_url(
    extra: Annotated[
        str,
        Doc("""
            Extra state params encoded as a JSON string. Will be returned when redirected back to the FE.
        """),
    ],
    request: Request,
):
    return await Account.create_social_auth_session(request=request, extra=extra, provider="google")


@me_router.get(
    "/me/auth/google/callback/{nonce}",
    summary="Google Auth Callback",
    response_class=RedirectResponse,
)
async def google_auth_callback(
    nonce: Annotated[
        str,
        Doc("""
            The nonce generated from the auth session initially.
        """),
    ],
    code: Annotated[
        str,
        Doc("""
            The authorization code from Google.
        """),
    ],
):
    session = await Account.get_auth_session(nonce=nonce)
    email, name, picture = await Account.authorize_google(code=code, session=session)
    await Account.maybe_create_user(email=email, name=name, picture=picture, session=session)

    fe_redir_url = await Account.get_fe_redirect_url(session=session)

    return RedirectResponse(url=fe_redir_url, status_code=302)
