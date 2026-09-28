from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0004_auto_20260928_1851')]

    initial = False

    operations = [
        ops.AddField(
            model_name='EmailAccount',
            name='account_id',
            field=fields.CharField(max_length=128),
        ),
    ]
