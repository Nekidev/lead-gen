import asyncio

from datetime import datetime, timezone, timedelta

from lead_gen import zoho, settings
from lead_gen.database import Email


async def sending_task():
    while True:
        emails = (
            await Email.filter(is_sent=False, schedule__lt=datetime.now(timezone.utc))
            .select_for_update(nowait=True, skip_locked=True)
            .prefetch_related("account", "lead", "step__sequence")
        )

        print(f"Processing {len(emails)} emails.")

        for email in emails:
            if email.account.access_token_expires_at > datetime.now(timezone.utc) - timedelta(
                minutes=1
            ):
                try:
                    tokens = await zoho.refresh_tokens(
                        email.account.refresh_token,
                        settings.ZOHO_CLIENT_ID,
                        settings.ZOHO_CLIENT_SECRET,
                        email.account.accounts_server,
                    )
                except Exception as e:
                    print(f"Could not refresh account token: {e}")
                    continue

                email.account.access_token = tokens["access_token"]
                email.account.access_token_expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=tokens["expires_in"]
                )

                await email.account.save()

            reply_to_id = None
            if email.subject == "":
                last_email = (
                    await Email.filter(is_sent=True, step=email.step, lead=email.lead)
                    .order_by("-schedule")
                    .first()
                )

                if last_email is not None:
                    reply_to_id = last_email.message_id

            try:
                result = await zoho.send_email(
                    email.account.account_id,
                    email.account.access_token,
                    email.account.email,
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

                print(f"Sent email {email.id} from {email.account.email} to {email.lead.person_email}")

            except Exception as e:
                print(f"Could not send email: {e}")

        await asyncio.sleep(30)
