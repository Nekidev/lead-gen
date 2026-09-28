from typing import TypedDict

from httpx import AsyncClient

from urllib.parse import quote

from lead_gen import settings


_client = AsyncClient()


def get_redirect_uri() -> str:
    return f"https://accounts.zoho.com/oauth/v2/auth?client_id={quote(settings.ZOHO_CLIENT_ID)}&response_type=code&redirect_uri={quote(settings.ZOHO_REDIRECT_URI)}&scope=ZohoMail.messages.ALL+ZohoMail.accounts.READ&access_type=offline"


class ZohoTokens(TypedDict):
    access_token: str
    refresh_token: str
    api_domain: str
    token_type: str
    expires_in: int


async def get_tokens(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    accounts_server: str = "https://accounts.zoho.com",
) -> ZohoTokens:
    response = await _client.post(
        f"{accounts_server}/oauth/v2/token",
        params={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )
    response.raise_for_status()

    return response.json()


async def refresh_tokens(refresh_token: str, client_id: str, client_secret: str, accounts_server: str = "https://accounts.zoho.com") -> ZohoTokens:
    response = await _client.post(f"{accounts_server}/oauth/v2/token", params={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    })
    response.raise_for_status()

    data = response.json()
    data["refresh_token"] = refresh_token

    return data


async def get_accounts(access_token: str):
    pass