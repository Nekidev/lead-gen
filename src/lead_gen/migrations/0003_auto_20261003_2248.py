from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0002_auto_20261003_2247')]

    initial = False

    operations = [
        ops.AlterField(
            model_name='EmailAccount',
            name='name',
            field=fields.CharField(max_length=128),
        ),
    ]
