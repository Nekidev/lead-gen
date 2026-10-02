from tortoise import migrations
from tortoise.migrations import operations as ops
import datetime
from orjson import loads
from tortoise.fields.base import OnDelete
from tortoise.fields.data import JSON_DUMPS
from tortoise import fields
from tortoise.indexes import Index

class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name='EmailAccount',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('email', fields.CharField(max_length=128)),
                ('account_id', fields.CharField(unique=True, max_length=128)),
                ('token_type', fields.CharField(max_length=16)),
                ('access_token', fields.CharField(max_length=128)),
                ('access_token_expires_at', fields.DatetimeField(auto_now=False, auto_now_add=False)),
                ('refresh_token', fields.CharField(max_length=128)),
                ('accounts_server', fields.CharField(max_length=64)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'emailaccount', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
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
                ('is_enabled', fields.BooleanField(db_default=False)),
                ('send_time_from', fields.DatetimeField(db_default=datetime.datetime.fromisoformat('1970-01-01T09:00:00+00:00'), auto_now=False, auto_now_add=False)),
                ('send_time_to', fields.DatetimeField(db_default=datetime.datetime.fromisoformat('1970-01-01T16:00:00+00:00'), auto_now=False, auto_now_add=False)),
                ('send_days', fields.JSONField(db_default=[], encoder=JSON_DUMPS, decoder=loads)),
                ('email_daily_max', fields.IntField(db_default=10)),
                ('email_bcc', fields.CharField(null=True, max_length=64)),
                ('email_accounts', fields.ManyToManyField('models.EmailAccount', unique=True, db_constraint=True, through='sequence_emailaccount', forward_key='emailaccount_id', backward_key='sequence_id', related_name='sequences', on_delete=OnDelete.CASCADE)),
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
                ('account', fields.ForeignKeyField('models.EmailAccount', source_field='account_id', null=True, db_constraint=True, to_field='id', related_name='emails', on_delete=OnDelete.SET_NULL)),
                ('subject', fields.CharField(max_length=128)),
                ('content', fields.CharField(max_length=2048)),
                ('is_sent', fields.BooleanField(db_default=False)),
                ('is_priority', fields.BooleanField(db_default=False)),
                ('is_edited', fields.BooleanField(db_default=False)),
                ('schedule', fields.DatetimeField(null=True, auto_now=False, auto_now_add=False)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'email', 'app': 'models', 'unique_together': [('step', 'lead')], 'indexes': [Index(fields=['step'])], 'pk_attr': 'id'},
            bases=['Model'],
        ),
    ]
