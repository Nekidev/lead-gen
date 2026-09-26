from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields
from tortoise.migrations.constraints import UniqueConstraint

class Migration(migrations.Migration):
    dependencies = [('models', '0001_initial')]

    initial = False

    operations = [
        ops.AddField(
            model_name='Flag',
            name='index',
            field=fields.IntField(),
        ),
        ops.AddConstraint(
            model_name='Flag',
            constraint=UniqueConstraint(fields=('project', 'index'), name=None),
        ),
        ops.AddConstraint(
            model_name='Flag',
            constraint=UniqueConstraint(fields=('project', 'name'), name=None),
        ),
    ]
