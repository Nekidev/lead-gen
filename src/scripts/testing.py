import asyncio

from datetime import datetime, timezone, timedelta

from rich import print

from lead_gen import zoho, settings
from lead_gen.database import on_startup, on_shutdown, EmailAccount


async def main():
    await on_startup()

    account = await EmailAccount.first()
    if account.access_token_expires_at < datetime.now(timezone.utc):
        print("Refreshing access token...")
        tokens = await zoho.refresh_tokens(
            account.refresh_token,
            settings.ZOHO_CLIENT_ID,
            settings.ZOHO_CLIENT_SECRET,
            account.accounts_server,
        )
        account.access_token = tokens["access_token"]
        account.access_token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=tokens["expires_in"]
        )

        await account.save()

    # email = await zoho.send_email(
    #     account.account_id,
    #     account.access_token,
    #     account.email,
    #     "rafael@duckity.com",
    #     "",
    #     "",
    #     "Hey! Testing stuff",
    #     "Hey there, are you okay with receiving my emails?",
    # )
    # print(email)

    emails = await zoho.get_emails(
        account.account_id,
        account.access_token,
    )
    print(emails)

    await on_shutdown()


def run():
    asyncio.run(main())
