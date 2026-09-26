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


class Company(Model):
    id = fields.IntField(primary_key=True)

    name = fields.CharField(max_length=256, unique=True)
    website = fields.CharField(max_length=256)
    people: fields.BackwardFKRelation["Person"]

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)


class Person(Model):
    id = fields.IntField(primary_key=True)
    id_hunter = fields.IntField(unique=True)

    name = fields.CharField(max_length=256)
    role = fields.CharField(max_length=256)
    email = fields.CharField(max_length=256)
    company = fields.ForeignKeyField(Company, related_name="people")

    leads: fields.BackwardFKRelation["Lead"]
    emails: fields.BackwardFKRelation["Email"]

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)


class Project(Model):
    id = fields.IntField(primary_key=True)

    name = fields.CharField(max_length=64, unique=True)
    leads: fields.BackwardFKRelation["Lead"]
    templates: fields.BackwardFKRelation["EmailTemplate"]
    flags: fields.BackwardFKRelation["Flag"]

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)


class EmailTemplate(Model):
    id = fields.IntField(primary_key=True)

    name = fields.CharField(max_length=64)
    project = fields.ForeignKeyField(Project, related_name="templates")

    subject = fields.TextField()
    content = fields.TextField()

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)


class Email(Model):
    id = fields.IntField(primary_key=True)

    person = fields.ForeignKeyField(Person, related_name="emails")
    subject = fields.CharField(max_length=64)
    content = fields.CharField(max_length=256)

    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)


class Lead(Model):
    id = fields.IntField(primary_key=True)

    person = fields.ForeignKeyField(Person, related_name="leads")
    project = fields.ForeignKeyField(Project, related_name="leads")
    flags: fields.BackwardFKRelation["FlagValue"]

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


async def on_startup():
    await Tortoise.init(config=CONFIG)


async def on_shutdown():
    await Tortoise.close_connections()
