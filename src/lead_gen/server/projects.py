from typing import Annotated, Literal

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import HTTPException

from pydantic import BaseModel, Field

from tortoise import transactions
from tortoise.expressions import F

from lead_gen import hunter, zoho, emails
from lead_gen.website import env
from lead_gen.database import (
    Project,
    Lead,
    Flag,
    FlagValue,
    Sequence,
    Step,
    Email,
    Day,
    EmailAccount,
)
from lead_gen.scheduling import Rules, Calendar


router = APIRouter()


@router.get("/projects/create")
async def handle_get_project_create():
    page = env.get_template("projects-create.html.j2")
    response = HTMLResponse(page.render())
    return response


class CreateForm(BaseModel):
    name: str


@router.post("/projects/create")
@transactions.atomic()
async def handle_post_project_create(form: Annotated[CreateForm, Form()]):
    project = await Project.create(name=form.name)

    return RedirectResponse(f"/projects/{project.id}", status_code=303)


@router.get("/projects/{project_id:int}")
async def handle_get_project(project_id: int):
    project = await Project.get(id=project_id).prefetch_related(
        "flags", "sequences", "leads", "leads__flags__flag"
    )

    page = env.get_template("projects-get.html.j2")
    response = HTMLResponse(page.render(project=project))
    return response


class UpdateProject(BaseModel):
    name: str | None = None
    action: Literal["save", "delete"] = "save"


@router.post("/projects/{project_id:int}")
@transactions.atomic()
async def handle_post_project(project_id: int, form: Annotated[UpdateProject, Form()]):
    project = await Project.get(id=project_id)

    if form.action == "save":
        if form.name is not None:
            project.name = form.name

        await project.save()
        return RedirectResponse(f"/projects/{project_id}", status_code=303)

    else:
        await project.delete()
        return RedirectResponse("/", status_code=303)


@router.post("/projects/{project_id:int}/leads")
@transactions.atomic()
async def handle_post_project_leads(request: Request, project_id: int):
    form = await request.form()
    project = await Project.get(id=project_id)

    for key, value in form.items():
        if not key.startswith("flag-"):
            continue

        key = key.removeprefix("flag-")

        lead_id = int(key.split("-")[0])
        flag_id = int(key.split("-")[1])

        if value == "":
            await FlagValue.filter(flag_id=flag_id, lead_id=lead_id).delete()
        else:
            await FlagValue.update_or_create(
                flag_id=flag_id, lead_id=lead_id, defaults={"value": value}
            )

    response = RedirectResponse(f"/projects/{project.id}", status_code=303)
    return response


class ImportLeads(BaseModel):
    hunter_api_key: str = Field(alias="hunter-api-key")


@router.post("/projects/{project_id:int}/leads/import")
@transactions.atomic()
async def handle_post_project_leads_import(project_id: int, form: Annotated[ImportLeads, Form()]):
    project = await Project.get(id=project_id)

    leads = await hunter.list_leads(form.hunter_api_key)
    for lead in leads:
        await Lead.update_or_create(
            project=project,
            id_hunter=lead["id"],
            defaults={
                "person_name": f"{lead['first_name']} {lead['last_name']}",
                "person_role": lead["position"],
                "person_email": lead["email"],
                "company_name": lead["company"],
                "company_website": lead["website"],
            },
        )

    response = RedirectResponse(f"/projects/{project.id}", status_code=303)
    return response


@router.get("/projects/{project_id:int}/leads/create")
async def handle_get_project_leads_create(project_id: int):
    project = await Project.get(id=project_id).prefetch_related("flags")

    page = env.get_template("leads-create.html.j2")
    response = HTMLResponse(page.render(project=project))
    return response


class CreateLead(BaseModel):
    person_name: str = Field(alias="person-name")
    person_email: str = Field(alias="person-email")
    person_role: str = Field(alias="person-role")
    company_name: str = Field(alias="company-name")
    company_website: str = Field(alias="company-website")


@router.post("/projects/{project_id:int}/leads/create")
@transactions.atomic()
async def handle_post_project_leads_create(
    request: Request, project_id: int, form: Annotated[CreateLead, Form()]
):
    project = await Project.get(id=project_id).prefetch_related("flags")

    lead, _ = await Lead.update_or_create(
        project=project,
        person_name=form.person_name,
        company_name=form.company_name,
        defaults={
            "person_name": form.person_name,
            "person_email": form.person_email,
            "person_role": form.person_role,
            "company_name": form.company_name,
            "company_website": form.company_website,
        },
    )

    raw_form = await request.form()
    for key, value in raw_form.items():
        if not key.startswith("flag-") or not value:
            continue

        key = key.removeprefix("flag-")
        flag_id = int(key)

        await FlagValue.update_or_create(flag_id=flag_id, lead_id=lead.id, value=value)

    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@router.get("/projects/{project_id:int}/leads/{lead_id:int}")
async def handle_get_project_lead(project_id: int, lead_id: int):
    project = await Project.get(id=project_id).prefetch_related("flags")
    lead = await Lead.get(id=lead_id, project=project)

    page = env.get_template("leads-get.html.j2")
    response = HTMLResponse(page.render(project=project, lead=lead))
    return response


class UpdateLead(BaseModel):
    person_name: str | None = Field(None, alias="person-name")
    person_email: str | None = Field(None, alias="person-email")
    person_role: str | None = Field(None, alias="person-role")
    company_name: str | None = Field(None, alias="company-name")
    company_website: str | None = Field(None, alias="company-website")
    action: Literal["save", "delete"] = "save"


@router.post("/projects/{project_id:int}/leads/{lead_id:int}")
@transactions.atomic()
async def handle_post_project_lead(
    request: Request, project_id: int, lead_id: int, form: Annotated[UpdateLead, Form()]
):
    project = await Project.get(id=project_id)
    lead = await Lead.get(id=lead_id, project=project)

    if form.action == "delete":
        await lead.delete()
        return RedirectResponse(f"/projects/{project_id}", status_code=303)

    else:
        raw_form = await request.form()
        for key, value in raw_form.items():
            if form.person_name is not None:
                lead.person_name = form.person_name
            if form.person_role is not None:
                lead.person_role = form.person_role
            if form.person_email is not None:
                lead.person_email = form.person_email
            if form.company_name is not None:
                lead.company_name = form.company_name
            if form.company_website is not None:
                lead.company_website = form.company_website
            await lead.save()

            if not key.startswith("flag-"):
                continue

            key = key.removeprefix("flag-")
            flag_id = int(key)

            if value:
                await FlagValue.update_or_create(flag_id=flag_id, lead_id=lead.id, value=value)
            else:
                await FlagValue.filter(flag_id=flag_id, lead_id=lead_id).delete()

        return RedirectResponse(f"/projects/{project_id}/leads/{lead_id}", status_code=303)


@router.get("/projects/{project_id:int}/flags")
async def handle_get_project_flags(project_id: int):
    project = await Project.get(id=project_id).prefetch_related("flags")

    page = env.get_template("flags-edit.html.j2")
    response = HTMLResponse(page.render(project=project))
    return response


class CreateFlag(BaseModel):
    name: str


@router.post("/projects/{project_id:int}/flags/create")
async def handle_post_project_flags_create(project_id: int, form: Annotated[CreateFlag, Form()]):
    project = await Project.get(id=project_id).prefetch_related("flags")

    count = await project.flags.all().count()
    await Flag.create(project=project, name=form.name, default="", index=count)

    response = RedirectResponse(f"/projects/{project.id}/flags", status_code=303)
    return response


class UpdateFlag(BaseModel):
    name: str | None = None
    default: str | None = None
    action: Literal["save", "delete", "move-up", "move-down"] = "save"


@router.post("/projects/{project_id:int}/flags/{flag_id:int}")
@transactions.atomic()
async def handle_post_projects_flag_update(
    project_id: int, flag_id: int, form: Annotated[UpdateFlag, Form()]
):
    project = await Project.get(id=project_id)
    flag = await Flag.get(id=flag_id, project=project)

    match form.action:
        case "save":
            if form.name is not None:
                flag.name = form.name
            if form.default is not None:
                flag.default = form.default
            await flag.save()

        case "delete":
            await flag.delete()
            await Flag.filter(project=project, index__gt=flag.index).update(index=F("index") - 1)

        case "move-up":
            if flag.index > 0:
                other = await Flag.get(project=project, index=flag.index - 1)

                flag.index = -1  # prevent collission during the update
                await flag.save()

                flag.index = other.index
                other.index += 1

                await other.save()
                await flag.save()

        case "move-down":
            other = await Flag.get_or_none(project=project, index=flag.index + 1)
            if other is not None:
                flag.index = -1  # prevent collission during the update
                await flag.save()

                other.index -= 1
                flag.index = other.index + 1
                await other.save()
                await flag.save()

    return RedirectResponse(f"/projects/{project_id}/flags", status_code=303)


@router.get("/projects/{project_id:int}/sequences/create")
async def handle_get_project_sequences_create(project_id: int):
    project = await Project.get(id=project_id)

    page = env.get_template("sequences-create.html.j2")
    response = HTMLResponse(page.render(project=project))
    return response


class CreateSequence(BaseModel):
    name: str


@router.post("/projects/{project_id:int}/sequences/create")
@transactions.atomic()
async def handle_post_project_sequences_create(
    project_id: int, form: Annotated[CreateSequence, Form()]
):
    project = await Project.get(id=project_id)
    sequence = await Sequence.create(project=project, name=form.name)

    return RedirectResponse(f"/projects/{project_id}/sequences/{sequence.id}", status_code=303)


@router.get("/projects/{project_id:int}/sequences/{sequence_id:int}")
async def handle_get_project_sequence(project_id: int, sequence_id: int):
    project = await Project.get(id=project_id)
    sequence = await Sequence.get(id=sequence_id, project=project).prefetch_related(
        "steps", "email_accounts"
    )
    accounts = await EmailAccount.all()

    page = env.get_template("sequences-get.html.j2")
    response = HTMLResponse(page.render(project=project, sequence=sequence, accounts=accounts))
    return response


class UpdateSequence(BaseModel):
    name: str | None = None
    toggle_sending_day: Day | None = Field(None, alias="toggle-sending-day")
    send_time_from: str | None = Field(None, alias="send-time-from")
    send_time_to: str | None = Field(None, alias="send-time-to")
    email_daily_max: int | None = Field(None, alias="email-daily-max")
    email_bcc: str | None = Field(None, alias="email-bcc")
    add_account: int | str | None = Field(None, alias="add-account")
    remove_account: int | str | None = Field(None, alias="remove-account")
    is_enabled: bool | None = Field(None, alias="is-enabled")
    action: Literal["save", "delete"] = "save"


def parse_time(value: str) -> tuple[int, int]:
    hour, minute = value.split(":")
    return int(hour), int(minute)


@router.post("/projects/{project_id:int}/sequences/{sequence_id:int}")
@transactions.atomic()
async def handle_post_project_sequence(
    project_id: int, sequence_id: int, form: Annotated[UpdateSequence, Form()]
):
    project = await Project.get(id=project_id)
    sequence = await Sequence.get(id=sequence_id, project=project)
    is_enabled = sequence.is_enabled

    if form.action == "save":
        if form.name is not None:
            sequence.name = form.name
        if form.toggle_sending_day is not None:
            if form.toggle_sending_day in sequence.send_days:
                sequence.send_days.remove(form.toggle_sending_day)
            else:
                sequence.send_days.append(form.toggle_sending_day)
        if form.send_time_from is not None:
            hour, minute = parse_time(form.send_time_from)
            sequence.send_time_from = datetime(
                1970, 1, 1, hour=hour, minute=minute, tzinfo=timezone.utc
            )
        if form.send_time_to is not None:
            hour, minute = parse_time(form.send_time_to)
            sequence.send_time_to = datetime(
                1970, 1, 1, hour=hour, minute=minute, tzinfo=timezone.utc
            )
        if form.email_bcc is not None:
            sequence.email_bcc = form.email_bcc
        if form.email_daily_max is not None:
            sequence.email_daily_max = form.email_daily_max
        if form.add_account is not None:
            account = await EmailAccount.get(id=form.add_account)
            await sequence.email_accounts.add(account)
        if form.remove_account is not None:
            account = await EmailAccount.get(id=form.remove_account)
            await sequence.email_accounts.remove(account)
        if form.is_enabled is not None:
            sequence.is_enabled = form.is_enabled

        await sequence.save()

        if sequence.is_enabled and not is_enabled:
            leads = await project.leads.all().prefetch_related("flags__flag")
            steps = await sequence.steps.all().order_by("index")
            accounts = await sequence.email_accounts.all()
            await project.fetch_related("flags")

            rules = Rules(
                time_from=sequence.send_time_from.time(),
                time_to=sequence.send_time_to.time(),
                days=[
                    {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}[day]
                    for day in sequence.send_days
                ],
                daily_max=sequence.email_daily_max,
            )
            calendar = Calendar(rules)

            for lead_i, lead in enumerate(leads):
                first_email_id = None
                first_email_account = None

                for step in steps:
                    email = await lead.emails.all().get_or_none(step=step)
                    if email is not None and email.is_sent:
                        if first_email_id is None:
                            first_email_id = calendar.insert(None, email.schedule).id
                        if first_email_account is None:
                            first_email_account = accounts[lead_i % len(accounts)]
                        continue

                    email = emails.get_rendered_email(project, step, lead, email)

                    if first_email_id is None:
                        event = calendar.schedule(None)
                        first_email_id = event.id
                        first_email_account = accounts[lead_i % len(accounts)]
                    else:
                        event = calendar.schedule(
                            None, after_id=first_email_id, after_time=timedelta(days=step.days)
                        )

                    await Email.update_or_create(
                        step=step,
                        lead=lead,
                        defaults={
                            "subject": email.subject,
                            "content": email.content,
                            "is_sent": email.is_sent,
                            "is_edited": email.is_edited,
                            "is_priority": email.is_priority,
                            "schedule": event.dt,
                            "account": first_email_account,
                        },
                    )

        elif not sequence.is_enabled and is_enabled:
            steps = await sequence.steps.all()

            for step in steps:
                await step.emails.filter(is_sent=False).update(schedule=None, account=None)
                await step.emails.filter(is_sent=False, is_edited=False).delete()

        return RedirectResponse(f"/projects/{project_id}/sequences/{sequence_id}", status_code=303)

    else:
        await sequence.delete()
        return RedirectResponse(f"/projects/{project_id}", status_code=303)


@router.get("/projects/{project_id:int}/sequences/{sequence_id:int}/connect/zoho")
async def handle_get_project_sequence_connect_zoho(project_id: int, sequence_id: int):
    response = RedirectResponse(zoho.get_redirect_uri())
    response.set_cookie("next", f"/projects/{project_id}/sequences/{sequence_id}", expires=900)
    return response


@router.get("/projects/{project_id:int}/sequences/{sequence_id:int}/steps/create")
async def handle_get_project_sequence_steps_create(project_id: int, sequence_id: int):
    project = await Project.get(id=project_id)
    sequence = await Sequence.get(id=sequence_id, project=project).prefetch_related("steps")

    default_days = len(sequence.steps) * 3

    page = env.get_template("steps-create.html.j2")
    response = HTMLResponse(
        page.render(project=project, sequence=sequence, default_days=default_days)
    )
    return response


class CreateStep(BaseModel):
    days: int
    name: str
    subject: str
    content: str


@router.post("/projects/{project_id:int}/sequences/{sequence_id:int}/steps/create")
@transactions.atomic()
async def handle_post_project_sequence_steps_create(
    project_id: int, sequence_id: int, form: Annotated[CreateStep, Form()]
):
    project = await Project.get(id=project_id)
    sequence = await Sequence.get(id=sequence_id, project=project)
    steps = await Step.filter(sequence=sequence).count()

    step = await Step.create(
        sequence=sequence,
        index=steps,
        days=form.days,
        name=form.name,
        subject=form.subject,
        content=form.content,
    )

    return RedirectResponse(
        f"/projects/{project_id}/sequences/{sequence_id}/steps/{step.id}", status_code=303
    )


@router.get("/projects/{project_id:int}/sequences/{sequence_id:int}/steps/{step_id:int}")
async def handle_get_project_sequence_steps(project_id: int, sequence_id: int, step_id: int):
    project = await Project.get(id=project_id).prefetch_related("flags")
    sequence = await Sequence.get(id=sequence_id, project=project)
    step = await Step.get(id=step_id, sequence=sequence)

    subject_error = emails.get_template_error(
        step.subject, emails.get_template_context(project, None)
    )
    content_error = emails.get_template_error(
        step.content, emails.get_template_context(project, None)
    )

    page = env.get_template("steps-edit.html.j2")
    response = HTMLResponse(
        page.render(
            project=project,
            sequence=sequence,
            step=step,
            subject_error=subject_error,
            content_error=content_error,
        )
    )
    return response


class UpdateStep(BaseModel):
    days: int | None = None
    name: str | None = None
    subject: str | None = None
    content: str | None = None
    action: Literal["save", "delete", "move-up", "move-down"] = "save"


@router.post("/projects/{project_id:int}/sequences/{sequence_id:int}/steps/{step_id:int}")
@transactions.atomic()
async def handle_post_project_sequence_steps(
    project_id: int, sequence_id: int, step_id: int, form: Annotated[UpdateStep, Form()]
):
    project = await Project.get(id=project_id)
    sequence = await Sequence.get(id=sequence_id, project=project)
    step = await Step.get(id=step_id, sequence=sequence)

    match form.action:
        case "save":
            if form.days is not None:
                step.days = form.days
            if form.name is not None:
                step.name = form.name
            if form.subject is not None:
                step.subject = form.subject
            if form.content is not None:
                step.content = form.content
            await step.save()

            return RedirectResponse(
                f"/projects/{project_id}/sequences/{sequence_id}/steps/{step_id}", status_code=303
            )

        case "delete":
            await step.delete()
            await Step.filter(sequence=sequence, index__gt=step.index).update(index=F("index") - 1)
            return RedirectResponse(
                f"/projects/{project_id}/sequences/{sequence_id}", status_code=303
            )

        case "move-up":
            if step.index > 0:
                other = await Step.get(sequence=sequence, index=step.index - 1)

                step_days = step.days
                other_days = other.days
                other_index = other.index

                step.days = -1
                step.index = -1
                await step.save()

                other.days = step_days
                other.index += 1
                await other.save()

                step.days = other_days
                step.index = other_index
                await step.save()

            return RedirectResponse(
                f"/projects/{project_id}/sequences/{sequence_id}", status_code=303
            )

        case "move-down":
            other = await Step.get_or_none(sequence=sequence, index=step.index + 1)
            if other is not None:
                step_days = step.days
                other_days = other.days
                other_index = other.index

                step.days = -1
                step.index = -1
                await step.save()

                other.days = step_days
                other.index -= 1
                await other.save()

                step.days = other_days
                step.index = other_index
                await step.save()

            return RedirectResponse(
                f"/projects/{project_id}/sequences/{sequence_id}", status_code=303
            )


@router.get("/projects/{project_id:int}/sequences/{sequence_id:int}/steps/{step_id:int}/emails")
async def handle_get_project_sequence_step_emails(project_id: int, sequence_id: int, step_id: int):
    project = await Project.get(id=project_id).prefetch_related("leads__flags__flag")
    sequence = await Sequence.get(id=sequence_id, project=project)
    step = await Step.get(id=step_id, sequence=sequence).prefetch_related("emails")

    lead_to_email = {email.lead_id: email for email in step.emails}
    email_list = []
    for lead in project.leads:
        email = lead_to_email.get(lead.id)
        email_list.append(emails.get_rendered_email(project, step, lead, email))

    page = env.get_template("steps-emails.html.j2")
    response = HTMLResponse(
        page.render(project=project, sequence=sequence, step=step, emails=email_list)
    )
    return response


@router.get(
    "/projects/{project_id:int}/sequences/{sequence_id:int}/steps/{step_id:int}/emails/{lead_id:int}"
)
async def handle_get_project_sequence_step_emails_email(
    project_id: int, sequence_id: int, step_id: int, lead_id: int
):
    project = await Project.get(id=project_id)
    sequence = await Sequence.get(id=sequence_id, project=project)
    step = await Step.get(id=step_id, sequence=sequence)
    lead = await Lead.get(id=lead_id, project=project).prefetch_related("flags__flag")
    email = await Email.get_or_none(step=step, lead=lead)

    email = emails.get_rendered_email(project, step, lead, email)

    page = env.get_template("steps-emails-get.html.j2")
    response = HTMLResponse(
        page.render(project=project, sequence=sequence, step=step, lead=lead, email=email)
    )
    return response


class UpdateEmail(BaseModel):
    subject: str | None = None
    content: str | None = None
    is_priority: bool | None = None
    action: Literal["save", "delete"] = "save"


@router.post(
    "/projects/{project_id:int}/sequences/{sequence_id:int}/steps/{step_id:int}/emails/{lead_id:int}"
)
@transactions.atomic()
async def handle_post_project_sequence_step_emails_email(
    project_id: int,
    sequence_id: int,
    step_id: int,
    lead_id: int,
    form: Annotated[UpdateEmail, Form()],
):
    project = await Project.get(id=project_id)
    sequence = await Sequence.get(id=sequence_id, project=project)
    step = await Step.get(id=step_id, sequence=sequence)
    lead = await Lead.get(id=lead_id, project=project).prefetch_related("flags__flag")
    email = await Email.get_or_none(lead=lead, step=step)

    if form.action == "save":
        if email is not None:
            if email.is_sent:
                raise HTTPException(409, "You cannot edit a sent email!")

            if form.subject is not None:
                email.subject = form.subject
            if form.content is not None:
                email.content = form.content
            if form.is_priority is not None:
                email.is_priority = form.is_priority

            await email.save()

        else:
            rendered = emails.get_rendered_email(project, step, lead, None)

            await Email.create(
                step=step,
                lead=lead,
                subject=form.subject | rendered.subject,
                content=form.content | rendered.content,
                is_edited=True,
                is_priority=form.is_priority or False,
            )

    else:
        # Don't allow deleting already-sent emails.
        await Email.filter(step=step, lead=lead).delete()

    return RedirectResponse(
        f"/projects/{project_id}/sequences/{sequence_id}/steps/{step_id}/emails/{lead_id}",
        status_code=303,
    )
