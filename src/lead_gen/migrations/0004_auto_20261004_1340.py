from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0003_auto_20261003_2248')]

    initial = False

    operations = [
        ops.AddField(
            model_name='Step',
            name='transform_dedent',
            field=fields.BooleanField(db_default=False),
        ),
        ops.AddField(
            model_name='Step',
            name='transform_deduplicate_blank_lines',
            field=fields.BooleanField(db_default=False),
        ),
    ]
