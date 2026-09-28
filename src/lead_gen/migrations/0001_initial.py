from tortoise import migrations
from tortoise.migrations import operations as ops
import datetime
from lead_gen.database import Day
from orjson import loads
from tortoise.fields.base import OnDelete
from tortoise.fields.data import JSON_DUMPS
from tortoise import fields

class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name='Project',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('name', fields.CharField(unique=True, max_length=64)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'project', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Flag',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('index', fields.IntField()),
                ('name', fields.CharField(max_length=64)),
                ('default', fields.CharField(max_length=64)),
                ('project', fields.ForeignKeyField('models.Project', source_field='project_id', db_constraint=True, to_field='id', related_name='flags', on_delete=OnDelete.CASCADE)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'flag', 'app': 'models', 'unique_together': [('project', 'index'), ('project', 'name')], 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Lead',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('id_hunter', fields.IntField(null=True)),
                ('project', fields.ForeignKeyField('models.Project', source_field='project_id', db_constraint=True, to_field='id', related_name='leads', on_delete=OnDelete.CASCADE)),
                ('person_name', fields.CharField(max_length=64)),
                ('person_role', fields.CharField(max_length=64)),
                ('person_email', fields.CharField(max_length=64)),
                ('company_name', fields.CharField(max_length=64)),
                ('company_website', fields.CharField(max_length=64)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'lead', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='FlagValue',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('flag', fields.ForeignKeyField('models.Flag', source_field='flag_id', db_constraint=True, to_field='id', related_name='values', on_delete=OnDelete.CASCADE)),
                ('lead', fields.ForeignKeyField('models.Lead', source_field='lead_id', db_constraint=True, to_field='id', related_name='flags', on_delete=OnDelete.CASCADE)),
                ('value', fields.CharField(max_length=64)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'flagvalue', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Sequence',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('name', fields.CharField(max_length=64)),
                ('project', fields.ForeignKeyField('models.Project', source_field='project_id', db_constraint=True, to_field='id', related_name='sequences', on_delete=OnDelete.CASCADE)),
                ('schedule_from', fields.DatetimeField(db_default=datetime.datetime.fromisoformat('1970-01-01T09:00:00+00:00'), auto_now=False, auto_now_add=False)),
                ('schedule_to', fields.DatetimeField(db_default=datetime.datetime.fromisoformat('1970-01-01T16:00:00+00:00'), auto_now=False, auto_now_add=False)),
                ('schedule_days', fields.JSONField(default=[Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI], encoder=JSON_DUMPS, decoder=loads)),
                ('sending_daily_max', fields.IntField(db_default=10)),
                ('sending_bcc', fields.CharField(null=True, max_length=64)),
                ('sending_token', fields.CharField(null=True, max_length=128)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'sequence', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Step',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('sequence', fields.ForeignKeyField('models.Sequence', source_field='sequence_id', db_constraint=True, to_field='id', related_name='steps', on_delete=OnDelete.CASCADE)),
                ('index', fields.IntField(db_index=True)),
                ('days', fields.IntField()),
                ('name', fields.CharField(max_length=64)),
                ('subject', fields.TextField(unique=False)),
                ('content', fields.TextField(unique=False)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'step', 'app': 'models', 'unique_together': [('sequence', 'index'), ('sequence', 'days')], 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Email',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('step', fields.ForeignKeyField('models.Step', source_field='step_id', db_constraint=True, to_field='id', related_name='emails', on_delete=OnDelete.CASCADE)),
                ('lead', fields.ForeignKeyField('models.Lead', source_field='lead_id', db_constraint=True, to_field='id', related_name='emails', on_delete=OnDelete.CASCADE)),
                ('subject', fields.CharField(max_length=128)),
                ('content', fields.CharField(max_length=2048)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'email', 'app': 'models', 'unique_together': [('step', 'lead')], 'pk_attr': 'id'},
            bases=['Model'],
        ),
    ]
