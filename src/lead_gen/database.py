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


class EmailAccount(Model):
    id = fields.IntField(primary_key=True)

    name = fields.CharField(max_length=128)
    email = fields.CharField(max_length=128)
    account_id = fields.CharField(max_length=128, unique=True)
    token_type = fields.CharField(max_length=16)
    access_token = fields.CharField(max_length=128)
    access_token_expires_at = fields.DateTimeField()
    refresh_token = fields.CharField(max_length=128)
    accounts_server = fields.CharField(max_length=64)

    emails: fields.BackwardFKRelation["Email"]
    sequences: fields.ManyToManyRelation["Sequence"]

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)


class Project(Model):
    id = fields.IntField(primary_key=True)

    name = fields.CharField(max_length=64, unique=True)
    leads: fields.BackwardFKRelation["Lead"]
    flags: fields.BackwardFKRelation["Flag"]
    sequences: fields.BackwardFKRelation["Sequence"]

    last_lead_tagged = fields.DateTimeField(null=True)

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

    emails: fields.BackwardFKRelation["Email"]

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
    is_enabled = fields.BooleanField(db_default=False)

    steps: fields.BackwardFKRelation["Step"]

    # sqlite doesn't support time-only fields so we use datetime set to utc epoch date
    send_time_from = fields.DateTimeField(
        db_default=datetime(year=1970, month=1, day=1, hour=9, tzinfo=timezone.utc)
    )
    send_time_to = fields.DateTimeField(
        db_default=datetime(year=1970, month=1, day=1, hour=16, tzinfo=timezone.utc)
    )
    send_days = fields.JSONField[list[Day]](db_default=[])

    email_daily_max = fields.IntField(db_default=10)
    email_bcc = fields.CharField(max_length=64, null=True)
    email_accounts = fields.ManyToManyField(EmailAccount, related_name="sequences")

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

    transform_dedent = fields.BooleanField(db_default=False)
    transform_deduplicate_blank_lines = fields.BooleanField(db_default=False)

    emails: fields.BackwardFKRelation["Email"]

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("sequence", "index"), ("sequence", "days")]


class EmailKind(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class Email(Model):
    id = fields.IntField(primary_key=True)
    message_id = fields.CharField(max_length=64, null=True, unique=True)
    """The Zoho message ID of this email.
    
    It will always be set when `is_sent` is set to `True`.
    """

    sequence = fields.ForeignKeyField(Sequence, related_name="emails")
    step = fields.ForeignKeyField(Step, related_name="emails", null=True)
    lead = fields.ForeignKeyField(Lead, related_name="emails")
    account = fields.ForeignKey(
        EmailAccount, related_name="emails", null=True, on_delete=fields.SET_NULL
    )

    kind = fields.CharEnumField(EmailKind, db_default=EmailKind.OUTGOING)

    subject = fields.CharField(max_length=128)
    content = fields.CharField(max_length=2048)

    is_sent = fields.BooleanField(db_default=False)
    "Whether the email was sent."
    is_edited = fields.BooleanField(db_default=False)
    "Whether the email's contents were edited or whether they were rendered directly from a template."
    is_priority = fields.BooleanField(db_default=False)
    "Whether the email's sending should be prioritized."
    is_cancelled = fields.BooleanField(db_default=False)
    "Whether the email's sending was cancelled (due to the prospect responding)."

    schedule = fields.DateTimeField(null=True)
    """The day and time this email is scheduled to be sent.
    
    Will always be set when the email has `is_sent == True`.
    """

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("step", "lead")]
        indexes = [("step", "kind"), ("kind", "schedule", "is_sent", "is_cancelled")]


async def on_startup():
    await Tortoise.init(config=CONFIG)


async def on_shutdown():
    await Tortoise.close_connections()
