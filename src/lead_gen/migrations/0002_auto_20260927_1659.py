from tortoise import migrations
from tortoise.migrations import operations as ops
from lead_gen.database import Day
from orjson import loads
from tortoise.fields.data import JSON_DUMPS
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0001_initial')]

    initial = False

    operations = [
        ops.AlterField(
            model_name='Sequence',
            name='schedule_days',
            field=fields.JSONField(db_default=[Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI], encoder=JSON_DUMPS, decoder=loads),
        ),
    ]
