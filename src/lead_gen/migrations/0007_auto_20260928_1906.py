from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0006_auto_20260928_1901')]

    initial = False

    operations = [
        ops.AlterField(
            model_name='EmailAccount',
            name='account_id',
            field=fields.CharField(unique=True, max_length=128),
        ),
    ]
