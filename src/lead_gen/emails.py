from datetime import datetime

from dataclasses import dataclass

from jinja2.sandbox import SandboxedEnvironment
from jinja2.exceptions import TemplateError, SecurityError

from lead_gen.database import Project, Lead, Email, Step


def get_sandbox_environment():
    env = SandboxedEnvironment(autoescape=False)
    env.filters["split"] = str.split
    return env


def get_template_error(template: str, context: dict) -> str | None:
    env = get_sandbox_environment()

    try:
        env.from_string(template).render(**context)
    except (TemplateError, SecurityError, Exception) as e:
        return e.message if hasattr(e, "message") else str(e)


def get_template_context(project: Project, lead: Lead | None):
    if lead is None:
        return {
            "lead": {
                "person_name": "",
                "person_role": "",
                "person_email": "",
                "company_name": "",
                "company_website": "",
            },
            "flags": {flag.name: flag.default for flag in project.flags},
        }

    else:
        flags = {}
        for flag in project.flags:
            flags[flag.name] = flag.default
            for value in lead.flags:
                if value.flag_id == flag.id:
                    if value.value:
                        flags[flag.name] = value.value

        return {
            "lead": {
                "person_name": lead.person_name,
                "person_role": lead.person_role,
                "person_email": lead.person_email,
                "company_name": lead.company_name,
                "company_website": lead.company_website,
            },
            "flags": flags,
        }


@dataclass
class RenderedEmail:
    lead: Lead
    error: str | None
    subject: str | None
    content: str | None
    schedule: datetime | None
    is_sent: bool
    is_edited: bool
    is_priority: bool
    is_cancelled: bool


def get_rendered_email(project: Project, step: Step, lead: Lead, email: Email | None):
    if email is not None:
        return RenderedEmail(
            lead=lead,
            error=None,
            subject=email.subject,
            content=email.content,
            schedule=email.schedule,
            is_sent=email.is_sent,
            is_edited=email.is_edited,
            is_priority=email.is_priority,
            is_cancelled=email.is_cancelled,
        )

    else:
        environment = get_sandbox_environment()
        context = get_template_context(project, lead)

        error = None
        subject = None
        content = None

        try:
            subject = environment.from_string(step.subject).render(context)
            content = environment.from_string(step.content).render(context)
        except (SecurityError, TemplateError) as e:
            error = e.message

        return RenderedEmail(
            lead=lead,
            error=error,
            subject=subject,
            content=content,
            schedule=None,
            is_sent=False,
            is_edited=False,
            is_priority=False,
            is_cancelled=False,
        )
