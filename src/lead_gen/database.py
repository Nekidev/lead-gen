from enum import Enum

from datetime import datetime, timezone

from tortoise import fields, Tortoise
from tortoise.models import Model


CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {"file_path": "db.sqlite3"},
        },
    },
    "apps": {
        "models": {
            "models": ["lead_gen.database"],
            "default_connection": "default",
            "migrations": "lead_gen.migrations",
        }
    },
}


class Project(Model):
    id = fields.IntField(primary_key=True)

    name = fields.CharField(max_length=64, unique=True)
    leads: fields.BackwardFKRelation["Lead"]
    flags: fields.BackwardFKRelation["Flag"]
    sequences: fields.BackwardFKRelation["Sequence"]

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)


class Lead(Model):
    id = fields.IntField(primary_key=True)
    id_hunter = fields.IntField(null=True)

    project = fields.ForeignKeyField(Project, related_name="leads")
    flags: fields.BackwardFKRelation["FlagValue"]

    person_name = fields.CharField(max_length=64)
    person_role = fields.CharField(max_length=64)
    person_email = fields.CharField(max_length=64)
    company_name = fields.CharField(max_length=64)
    company_website = fields.CharField(max_length=64)

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)


class Flag(Model):
    id = fields.IntField(primary_key=True)

    index = fields.IntField()
    name = fields.CharField(max_length=64)
    default = fields.CharField(max_length=64)
    project = fields.ForeignKey(Project, related_name="flags")
    values: fields.BackwardFKRelation["FlagValue"]

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)

    class Meta:
        index = [("project", "index")]
        unique_together = [("project", "index"), ("project", "name")]


class FlagValue(Model):
    id = fields.IntField(primary_key=True)

    flag = fields.ForeignKey(Flag, related_name="values")
    lead = fields.ForeignKey(Lead, related_name="flags")

    value = fields.CharField(max_length=64)

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)


class Day(str, Enum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


class Sequence(Model):
    id = fields.IntField(primary_key=True)

    name = fields.CharField(max_length=64)
    project = fields.ForeignKeyField(Project, related_name="sequences")

    steps: fields.BackwardFKRelation["Step"]

    # sqlite doesn't support time-only fields so we use datetime set to utc epoch date
    send_time_from = fields.DateTimeField(
        db_default=datetime(year=1970, month=1, day=1, hour=9, tzinfo=timezone.utc)
    )
    send_time_to = fields.DateTimeField(
        db_default=datetime(year=1970, month=1, day=1, hour=16, tzinfo=timezone.utc)
    )
    send_days = fields.JSONField[list[Day]](
        db_default=[Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI]
    )

    email_daily_max = fields.IntField(db_default=10)
    email_bcc = fields.CharField(max_length=64, null=True)

    zoho_access_token = fields.CharField(max_length=128, null=True)
    zoho_refresh_token = fields.CharField(max_length=128, null=True)
    zoho_email = fields.CharField(max_length=128, null=True)

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)


class Step(Model):
    id = fields.IntField(primary_key=True)

    sequence = fields.ForeignKeyField(Sequence, related_name="steps")

    index = fields.IntField(db_index=True)
    days = fields.IntField()
    name = fields.CharField(max_length=64)
    subject = fields.TextField()
    content = fields.TextField()

    emails: fields.BackwardFKRelation["Email"]

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("sequence", "index"), ("sequence", "days")]


class Email(Model):
    id = fields.IntField(primary_key=True)

    step = fields.ForeignKeyField(Step, related_name="emails")
    lead = fields.ForeignKeyField(Lead, related_name="emails")

    subject = fields.CharField(max_length=128)
    content = fields.CharField(max_length=2048)

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("step", "lead")]


async def on_startup():
    await Tortoise.init(config=CONFIG)


async def on_shutdown():
    await Tortoise.close_connections()
