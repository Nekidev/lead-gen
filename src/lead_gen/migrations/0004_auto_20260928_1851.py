from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0003_auto_20260927_1710')]

    initial = False

    operations = [
        ops.CreateModel(
            name='EmailAccount',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('email', fields.CharField(max_length=128)),
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
        ops.AddField(
            model_name='Email',
            name='account',
            field=fields.ForeignKeyField('models.EmailAccount', source_field='account_id', null=True, db_constraint=True, to_field='id', related_name='emails', on_delete=OnDelete.SET_NULL),
        ),
        ops.RenameField(
            model_name='Sequence',
            old_name='email_token',
            new_name='zoho_access_token',
        ),
        ops.AddField(
            model_name='Sequence',
            name='zoho_email',
            field=fields.CharField(null=True, max_length=128),
        ),
        ops.AddField(
            model_name='Sequence',
            name='zoho_refresh_token',
            field=fields.CharField(null=True, max_length=128),
        ),
    ]
