from typing import Annotated, Literal

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from pydantic import BaseModel, Field

from tortoise import transactions
from tortoise.expressions import F

from lead_gen import hunter
from lead_gen.website import env
from lead_gen.database import Project, EmailTemplate, Company, Person, Lead, Flag, FlagValue


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
        "flags", "templates", "leads__person__company", "leads__flags__flag"
    )

    page = env.get_template("projects-get.html.j2")
    response = HTMLResponse(page.render(project=project))
    return response


class UpdateProject(BaseModel):
    name: str | None = None
    flags: str | None = None
    action: Literal["save", "delete"] = "save"


@router.post("/projects/{project_id:int}")
@transactions.atomic()
async def handle_post_project(project_id: int, form: Annotated[UpdateProject, Form()]):
    project = await Project.get(id=project_id)

    if form.action == "save":
        if form.name is not None:
            project.name = form.name

        if form.flags is not None:
            project.flags = list(map(lambda i: i.strip(), form.flags.split(",")))

        await project.save()
        await project.fetch_related("flags", "templates", "leads__person__company", "leads__flags")

        page = env.get_template("projects-get.html.j2")
        response = HTMLResponse(page.render(project=project))

    else:
        await project.delete()
        response = RedirectResponse("/", status_code=303)

    return response


@router.get("/projects/{project_id:int}/templates/create")
async def handle_get_project_template_create(project_id: int):
    project = await Project.get(id=project_id)

    page = env.get_template("templates-create.html.j2")
    response = HTMLResponse(page.render(project=project))
    return response


class CreateTemplate(BaseModel):
    name: str
    subject: str
    content: str


@router.post("/projects/{project_id:int}/templates/create")
@transactions.atomic()
async def handle_post_project_template_create(
    project_id: int, form: Annotated[CreateTemplate, Form()]
):
    project = await Project.get(id=project_id)
    template = await EmailTemplate.create(
        project=project, name=form.name, subject=form.subject, content=form.content
    )

    return RedirectResponse(f"/projects/{project.id}/templates/{template.id}", status_code=303)


@router.get("/projects/{project_id:int}/templates/{template_id:int}")
async def handle_get_project_template(project_id: int, template_id: int):
    project = await Project.get(id=project_id)
    template = await EmailTemplate.get(id=template_id, project=project)

    page = env.get_template("templates-edit.html.j2")
    response = HTMLResponse(page.render(project=project, template=template))
    return response


class UpdateTemplate(BaseModel):
    name: str | None = None
    subject: str | None = None
    content: str | None = None
    action: Literal["save", "delete"] = "save"


@router.post("/projects/{project_id:int}/templates/{template_id:int}")
@transactions.atomic()
async def handle_post_project_template(
    project_id: int, template_id: int, form: Annotated[UpdateTemplate, Form()]
):
    project = await Project.get(id=project_id)
    template = await EmailTemplate.get(id=template_id, project=project)

    if form.action == "save":
        if form.name is not None:
            template.name = form.name

        if form.subject is not None:
            template.subject = form.subject

        if form.content is not None:
            template.content = form.content

        await template.save()

        page = env.get_template("templates-edit.html.j2")
        response = HTMLResponse(page.render(project=project, template=template))

    else:
        await template.delete()
        response = RedirectResponse(f"/projects/{project.id}", status_code=303)

    return response


@router.post("/projects/{project_id:int}/leads")
@transactions.atomic()
async def handle_post_project_leads(request: Request, project_id: int):
    form = await request.form()
    project = await Project.get(id=project_id)

    for key, value in form.items():
        lead_id = int(key.split("-")[0])
        flag_id = int(key.split("-")[1])

        if value == "":
            print("saving as nothing")
            await FlagValue.filter(flag_id=flag_id, lead_id=lead_id).delete()
        else:
            print("creating")
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
        company, _ = await Company.update_or_create(
            name=lead["company"],
            defaults={
                "name": lead["company"],
                "website": lead["website"],
            },
        )
        person, _ = await Person.update_or_create(
            id_hunter=lead["id"],
            defaults={
                "id_hunter": lead["id"],
                "name": f"{lead['first_name']} {lead['last_name']}",
                "role": lead["position"],
                "email": lead["email"],
                "company": company,
            },
        )

        await Lead.get_or_create(person=person, project=project)

    response = RedirectResponse(f"/projects/{project.id}", status_code=303)
    return response


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
