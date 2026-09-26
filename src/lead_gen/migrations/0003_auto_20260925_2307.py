from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0002_auto_20260925_2224')]

    initial = False

    operations = [
        ops.AddField(
            model_name='FlagValue',
            name='value',
            field=fields.CharField(max_length=64),
        ),
    ]
