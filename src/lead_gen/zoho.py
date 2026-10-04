import email
from email.policy import default
from email.message import EmailMessage

from typing import TypedDict

from urllib.parse import quote

from httpx import AsyncClient

from lead_gen import settings


_client = AsyncClient()


def get_redirect_uri() -> str:
    return f"https://accounts.zoho.com/oauth/v2/auth?client_id={quote(settings.ZOHO_CLIENT_ID)}&response_type=code&redirect_uri={quote(settings.ZOHO_REDIRECT_URI)}&scope=ZohoMail.messages.ALL+ZohoMail.accounts.READ&access_type=offline&prompt=consent"


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


class ZohoSentEmail(TypedDict):
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
) -> ZohoSentEmail:
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
            "action": "reply" if reply_to_id is not None else None
        },
    )
    if not response.is_success:
        print(response.text)
    response.raise_for_status()

    return response.json()["data"]


class ZohoEmail(TypedDict):
    summary: str
    sentDateInGMT: str
    calendarType: int
    subject: str
    messageId: str
    threadId: str | None
    "May not be present if the email is not a reply. When set, this is the ID of the original message."
    threadCount: str
    "May not be present if the email is not a reply."
    flagId: str
    status: str
    status2: str
    priority: str
    hasInline: str
    toAddress: str
    folderId: str
    fromAddress: str
    hasAttachment: str
    size: str
    sender: str
    receivedTime: str


async def get_emails(
    account_id: str,
    account_token: str,
    start: int = 1,
    limit: int = 200,
    only_threaded: bool = True,
) -> list[ZohoEmail]:
    response = await _client.get(
        f"https://mail.zoho.com/api/accounts/{account_id}/messages/view",
        params={
            "includeto": "true",
            "start": start,
            "limit": limit,
            "threadedMails": str(only_threaded).lower(),
        },
        headers={
            "Authorization": f"Bearer {account_token}",
        },
    )
    response.raise_for_status()

    return response.json()["data"]


async def get_email(
    account_id: str | int,
    account_token: str,
    message_id: str | int,
) -> EmailMessage:
    response = await _client.get(
        f"https://mail.zoho.com/api/accounts/{account_id}/messages/{message_id}/originalmessage",
        headers={"Authorization": f"Bearer {account_token}"},
    )
    response.raise_for_status()

    content = response.json()["data"]["content"]
    message = email.message_from_string(content, policy=default)

    return message