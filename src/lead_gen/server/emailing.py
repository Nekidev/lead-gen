import asyncio

from datetime import datetime, timezone, timedelta

from lead_gen import zoho, settings
from lead_gen.database import Email, EmailKind, EmailAccount, Lead


async def sending_task():
    while True:
        emails = (
            await Email.filter(
                kind=EmailKind.OUTGOING,
                is_sent=False,
                is_cancelled=False,
                schedule__lt=datetime.now(timezone.utc),
            )
            .select_for_update(nowait=True, skip_locked=True)
            .prefetch_related("account", "lead", "step__sequence")
        )

        print(f"Processing {len(emails)} emails.")

        for email in emails:
            try:
                await refresh(email.account)
            except Exception as e:
                print(f"Could not refresh email account's access token: {e}")
                continue

            reply_to_id = None
            if email.subject.strip() == "":
                last_email = (
                    await Email.filter(
                        is_sent=True, sequence_id=email.sequence_id, lead_id=email.lead_id
                    )
                    .order_by("-schedule")
                    .first()
                )

                if last_email is not None:
                    reply_to_id = last_email.message_id
                    email.subject = f"Re: {last_email.subject}"
                    await email.save()

            try:
                result = await zoho.send_email(
                    email.account.account_id,
                    email.account.access_token,
                    f"{email.account.name} <{email.account.email}>",
                    email.lead.person_email,
                    "",
                    email.step.sequence.email_bcc or "",
                    email.subject,
                    email.content,
                    reply_to_id,
                )

                email.message_id = result["messageId"]
                email.is_sent = True

                await email.save()

                print(
                    f"Sent email {email.id} from {email.account.email} to {email.lead.person_email}"
                )

            except Exception as e:
                print(f"Could not send email: {e}")

        await asyncio.sleep(30)


async def receiving_task():
    while True:
        accounts = await EmailAccount.all()

        for account in accounts:
            try:
                await refresh(account)
            except Exception as e:
                print(f"Could not refresh email account token: {e}")
                continue

            emails: list[zoho.ZohoEmail] = []
            start = 1
            is_broken = False
            while True:
                print(f"Loading received emails for {account.email}")
                try:
                    result = await zoho.get_emails(account.account_id, account.access_token, start)
                except Exception as e:
                    print(f"Could not fetch emails for {account.email}: {e}")
                    is_broken = True
                    break

                emails += result
                if len(emails) == 200:
                    start += 200
                else:
                    break

            if is_broken:
                continue

            print(f"Loaded {len(emails)} emails received by {account.email}")

            for email in emails:
                print(email["fromAddress"], "->", email["toAddress"], "in", email.get("threadId"))

                if "threadId" not in email or email["threadId"] == email["messageId"]:
                    continue

                if await Email.filter(message_id=email["messageId"]).exists():
                    print("duplicate for", email["messageId"], "-", email["subject"])
                    continue

                lead = await Lead.get_or_none(
                    person_email=email["fromAddress"],
                    project__sequences__email_accounts=account,
                )
                if lead is None:
                    print("No lead for", email["fromAddress"])
                    continue

                original_id = email["threadId"]
                original = await Email.get_or_none(message_id=original_id)
                if original is None:
                    print("no original for", original_id, "-", email["subject"])
                    continue
                try:
                    original_email = await zoho.get_email(
                    account.account_id, account.access_token, email["messageId"]
                )
                except Exception as e:
                    print(f"Could not get email: {e}")
                    continue
                content = original_email.get_body(["plain", "html", "related"]).get_content()

                try:
                    await Email.create(
                        message_id=email["messageId"],
                        step=None,
                        lead=lead,
                        sequence_id=original.sequence_id,
                        account=account,
                        kind=EmailKind.INCOMING,
                        subject=email["subject"],
                        content=content,
                        schedule=datetime.fromtimestamp(
                            float(email["receivedTime"]) / 1000, timezone.utc
                        ),
                        is_sent=True,
                    )

                except Exception as e:
                    print(f"Could not store incoming email: {e}")

                try:
                    await lead.emails.filter(is_sent=False, kind=EmailKind.OUTGOING).update(
                        is_cancelled=True
                    )
                except Exception as e:
                    print(f"Could not cancel future outgoing emails: {e}")

        await asyncio.sleep(30)


async def refresh(account: EmailAccount):
    if account.access_token_expires_at < datetime.now(timezone.utc) - timedelta(minutes=1):
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
