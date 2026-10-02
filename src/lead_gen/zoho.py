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
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )
    response.raise_for_status()

    print(response.json())

    return response.json()


async def refresh_tokens(
    refresh_token: str,
    client_id: str,
    client_secret: str,
    accounts_server: str = "https://accounts.zoho.com",
) -> ZohoTokens:
    response = await _client.post(
        f"{accounts_server}/oauth/v2/token",
        params={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )
    response.raise_for_status()

    data = response.json()
    data["refresh_token"] = refresh_token

    return data


class ZohoAccount(TypedDict):
    mailboxAddress: str
    accountId: str
    firstName: str
    lastName: str
    displayName: str
    accountDisplayName: str
    enabled: bool


async def get_accounts(access_token: str) -> list[ZohoAccount]:
    response = await _client.get(
        "https://mail.zoho.com/api/accounts", headers={"Authorization": f"Bearer {access_token}"}
    )
    response.raise_for_status()

    return response.json()["data"]


class SentEmail(TypedDict):
    subject: str
    content: str
    messageId: str
    "The Zoho message ID we care about for replies."
    mailId: str
    "The domain-dependant email ID."
    fromAddress: str
    toAddress: str
    ccAddress: str
    bccAddress: str


async def send_email(
    account_id: str,
    account_token: str,
    email_from: str,
    email_to: str,
    cc: str | None,
    bcc: str | None,
    subject: str,
    content: str,
    reply_to_id: str | None = None,
) -> SentEmail:
    """Send an email.

    Args:
        account_id (str): The ID of the account to send the email with.
        account_token (str): The access token of the account.
        email_from (str): The email address to send this email from.
        email_to (str): The email address to send this email to.
        cc (str | None): A list of email addresses to send carbon copies to.
        bcc (str | None): A list of email addresses to send blind carbon copies to.
        subject (str): The email's subject.
        content (str): The email's content.
        reply_to_id (str | None, optional): The message ID of the email to reply to, if any. Defaults to None.

    Returns:
        SentEmail: The sent email's data.
    """

    if reply_to_id is None:
        url = f"https://mail.zoho.com/api/accounts/{account_id}/messages"
    else:
        url = f"https://mail.zoho.com/api/accounts/{account_id}/messages/{reply_to_id}"

    response = await _client.post(
        url,
        headers={
            # TODO: Bearer? Zoho-oauthtoken?
            "Authorization": f"Bearer {account_token}",
        },
        json={
            "fromAddress": email_from,
            "toAddress": email_to,
            "ccAddress": cc,
            "bccAddress": bcc,
            "subject": subject,
            "content": content,
            "mailFormat": "plaintext",
            "askReceipt": "no",
        },
    )
    response.raise_for_status()

    return response.json()["data"]
