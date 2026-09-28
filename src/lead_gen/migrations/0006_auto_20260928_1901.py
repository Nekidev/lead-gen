from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0005_auto_20260928_1852')]

    initial = False

    operations = [
        ops.AddField(
            model_name='Sequence',
            name='email_accounts',
            field=fields.ManyToManyField('models.EmailAccount', unique=True, db_constraint=True, through='sequence_emailaccount', forward_key='emailaccount_id', backward_key='sequence_id', related_name='sequences', on_delete=OnDelete.CASCADE),
        ),
        ops.RemoveField(model_name='Sequence', name='zoho_access_token'),
        ops.RemoveField(model_name='Sequence', name='zoho_email'),
        ops.RemoveField(model_name='Sequence', name='zoho_refresh_token'),
    ]
