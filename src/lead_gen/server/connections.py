from typing import Annotated

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Query, Cookie
from fastapi.responses import RedirectResponse

from tortoise import transactions

from lead_gen import zoho, settings
from lead_gen.database import EmailAccount


router = APIRouter()


@router.get("/oauth/zoho/callback")
@transactions.atomic()
async def handle_oauth_zoho_callback(
    code: str,
    location: str,
    accounts_server: Annotated[str, Query(alias="accounts-server")],
    next: Annotated[str, Cookie()] = "/",
):
    tokens = await zoho.get_tokens(
        client_id=settings.ZOHO_CLIENT_ID,
        client_secret=settings.ZOHO_CLIENT_SECRET,
        code=code,
        redirect_uri=settings.ZOHO_REDIRECT_URI,
        accounts_server=accounts_server,
    )
    accounts = await zoho.get_accounts(tokens["access_token"])

    for account in accounts:
        if not account["enabled"]:
            continue

        await EmailAccount.update_or_create(
            account_id=account["accountId"],
            defaults={
                "email": account["mailboxAddress"],
                "account_id": account["accountId"],
                "token_type": tokens["token_type"],
                "access_token": tokens["access_token"],
                "access_token_expires_at": datetime.now(timezone.utc)
                + timedelta(seconds=tokens["expires_in"]),
                "refresh_token": tokens["refresh_token"],
                "accounts_server": accounts_server,
            },
        )

    return RedirectResponse(next, status_code=303)
