from tortoise import migrations
from tortoise.migrations import operations as ops
from orjson import loads
from tortoise.fields.data import JSON_DUMPS
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0007_auto_20260928_1906')]

    initial = False

    operations = [
        ops.AlterField(
            model_name='Sequence',
            name='send_days',
            field=fields.JSONField(db_default=[], encoder=JSON_DUMPS, decoder=loads),
        ),
    ]
